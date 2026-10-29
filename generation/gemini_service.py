"""
Centralized Resilient Gemini Service Layer.

Production-grade wrapper around Google GenAI SDK:
1. Multi-tier model fallback (Primary Lite -> Secondary Lite -> Tertiary / Final Fallback).
2. Exponential backoff with random jitter for transient errors (503 UNAVAILABLE, 429 RESOURCE_EXHAUSTED, timeouts).
3. Hard retry budget per model (does NOT retry unavailable models indefinitely).
4. Request timeouts via concurrent execution to prevent application hangs.
5. In-memory request deduplication and response caching.
6. API client pooling and reuse.
7. Structured logging of model, attempt, error type, and fallback transitions (Never logs secrets/keys).
8. Clean application-level exception handling without leaking raw API secrets.
"""

import os
import sys
import time
import json
import re
import random
import logging
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from google import genai
from config.gemini_config import GeminiConfig, sanitize_model_name, mask_secret

# Configure structured logger for Gemini Service
logger = logging.getLogger("GeminiService")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [GeminiService] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class GeminiServiceUnavailableError(Exception):
    """Raised when all Gemini models in the fallback cascade are temporarily unavailable."""
    def __init__(self, message: str, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.last_error = last_error


class GeminiService:
    """
    Centralized, resilient service for executing Gemini API requests.
    Implements singleton client reuse, deduplication, backoff + jitter, and model cascade.
    """

    _instance: Optional["GeminiService"] = None
    _clients: Dict[str, genai.Client] = {}

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GeminiConfig.get_api_key()
        self._cache: Dict[str, Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)

    @classmethod
    def get_instance(cls, api_key: Optional[str] = None) -> "GeminiService":
        """Singleton accessor for GeminiService."""
        if cls._instance is None:
            cls._instance = cls(api_key=api_key)
        return cls._instance

    def _get_client(self) -> genai.Client:
        """Reuses or initializes a genai.Client for the configured API key."""
        key = self.api_key
        if key not in self._clients:
            self._clients[key] = genai.Client(api_key=key)
        return self._clients[key]

    @staticmethod
    def _is_transient_error(error: Exception) -> Tuple[bool, str]:
        """
        Determines if an error is temporary/retryable (503, 429, timeout, connection drop).
        Returns (is_transient, error_code_or_status).
        """
        err_str = str(error).upper()

        if "503" in err_str or "UNAVAILABLE" in err_str:
            return True, "503_UNAVAILABLE"
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "RATE_LIMIT" in err_str:
            return True, "429_RESOURCE_EXHAUSTED"
        if "500" in err_str or "INTERNAL" in err_str:
            return True, "500_INTERNAL_SERVER_ERROR"
        if "502" in err_str or "BAD_GATEWAY" in err_str:
            return True, "502_BAD_GATEWAY"
        if "504" in err_str or "GATEWAY_TIMEOUT" in err_str:
            return True, "504_GATEWAY_TIMEOUT"
        if "TIMEOUT" in err_str or isinstance(error, (TimeoutError, FutureTimeoutError)):
            return True, "REQUEST_TIMEOUT"
        if "CONNECTION" in err_str or "REMOTE_DISCONNECTED" in err_str:
            return True, "CONNECTION_DROPPED"

        return False, "NON_RETRYABLE_ERROR"

    def _compute_cache_key(self, contents: Any, is_strong_task: bool) -> str:
        """Generates a stable cache key to prevent redundant Gemini API calls."""
        hasher = hashlib.sha256()
        hasher.update(str(is_strong_task).encode("utf-8"))
        if isinstance(contents, str):
            hasher.update(contents.encode("utf-8"))
        elif isinstance(contents, list):
            for item in contents:
                if isinstance(item, str):
                    hasher.update(item.encode("utf-8"))
                elif hasattr(item, "tobytes"):
                    hasher.update(item.tobytes()[:1024])
                else:
                    hasher.update(str(type(item)).encode("utf-8"))
        else:
            hasher.update(str(contents).encode("utf-8"))
        return hasher.hexdigest()

    def generate_content(
        self,
        contents: Any,
        is_strong_task: bool = False,
        timeout: Optional[float] = None,
        bypass_cache: bool = False,
    ) -> str:
        """
        Executes Gemini content generation with multi-model fallback, retry backoff, and timeouts.
        Returns the raw string output.
        """
        # Check cache if enabled
        cache_key = self._compute_cache_key(contents, is_strong_task)
        if GeminiConfig.ENABLE_RESPONSE_CACHE and not bypass_cache:
            if cache_key in self._cache:
                logger.debug("Returning cached Gemini response for request hash %s...", cache_key[:8])
                return self._cache[cache_key]

        cascade = GeminiConfig.get_model_cascade(is_strong_task=is_strong_task)
        timeout_sec = timeout or GeminiConfig.REQUEST_TIMEOUT_SECONDS
        client = self._get_client()

        last_exception: Optional[Exception] = None
        last_error_type: str = "UNKNOWN"

        for model_idx, model_name in enumerate(cascade):
            max_retries = GeminiConfig.MAX_RETRIES_PER_MODEL
            model_succeeded = False

            for attempt in range(1, max_retries + 1):
                logger.info(
                    "Attempting model='%s' [attempt %d/%d, cascade_tier=%d/%d]...",
                    model_name,
                    attempt,
                    max_retries,
                    model_idx + 1,
                    len(cascade)
                )

                try:
                    # Run generate_content with timeout
                    future = self._executor.submit(
                        client.models.generate_content,
                        model=model_name,
                        contents=contents
                    )
                    response = future.result(timeout=timeout_sec)
                    response_text = response.text.strip() if response and response.text else ""

                    logger.info(
                        "Model '%s' successfully completed request (output length: %d chars).",
                        model_name,
                        len(response_text)
                    )

                    # Cache successful result
                    if GeminiConfig.ENABLE_RESPONSE_CACHE:
                        if len(self._cache) >= GeminiConfig.MAX_CACHE_SIZE:
                            # Evict oldest item
                            self._cache.pop(next(iter(self._cache)))
                        self._cache[cache_key] = response_text

                    return response_text

                except Exception as exc:
                    last_exception = exc
                    is_transient, error_type = self._is_transient_error(exc)
                    last_error_type = error_type

                    logger.warning(
                        "Model '%s' failed on attempt %d with error_type='%s'.",
                        model_name,
                        attempt,
                        error_type
                    )

                    # If not transient (e.g. 404 NOT_FOUND, 400 INVALID_ARGUMENT), do not retry this model
                    if not is_transient:
                        logger.warning(
                            "Error is non-retryable on model '%s'. Moving immediately to fallback model...",
                            model_name
                        )
                        break

                    # If transient and retries remain, compute exponential backoff with jitter
                    if attempt < max_retries:
                        base_delay = GeminiConfig.BASE_RETRY_DELAY_SEC * (2 ** (attempt - 1))
                        jitter = base_delay * GeminiConfig.JITTER_FACTOR * (random.random() * 2.0 - 1.0)
                        delay = min(GeminiConfig.MAX_RETRY_DELAY_SEC, max(0.2, base_delay + jitter))
                        logger.info(
                            "Applying backoff + jitter for model '%s': waiting %.2fs before retry...",
                            model_name,
                            delay
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            "Model '%s' exhausted all %d retries.",
                            model_name,
                            max_retries
                        )

            # Announce fallback switch if more models exist in cascade
            if model_idx + 1 < len(cascade):
                next_model = cascade[model_idx + 1]
                logger.info(
                    "Switching to fallback model '%s' (Tier %d -> Tier %d)...",
                    next_model,
                    model_idx + 1,
                    model_idx + 2
                )

        # If every model in the cascade failed
        masked_key = GeminiConfig.get_masked_api_key()
        msg = (
            f"All configured Gemini models ({', '.join(cascade)}) are temporarily unavailable "
            f"due to upstream capacity or network limits (Last Error: {last_error_type}). "
            f"Active API key [{masked_key}]."
        )
        logger.error("Request failed across all fallback models: %s", msg)
        raise GeminiServiceUnavailableError(msg, last_error=last_exception)

    def generate_json(
        self,
        contents: Any,
        is_strong_task: bool = False,
        timeout: Optional[float] = None,
        bypass_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Executes Gemini content generation and parses the output as a strict JSON object.
        Gracefully strips markdown backticks or extracts using regex.
        """
        raw_text = self.generate_content(
            contents=contents,
            is_strong_task=is_strong_task,
            timeout=timeout,
            bypass_cache=bypass_cache
        )

        clean_text = raw_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(clean_text)
        except Exception:
            # Fallback regex search for JSON object or array
            match = re.search(r"(\{|\[).*(?:\}|\])", clean_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Failed to parse Gemini output as JSON: {clean_text[:200]}")


def get_gemini_service() -> GeminiService:
    """Helper to retrieve the centralized GeminiService singleton."""
    return GeminiService.get_instance()
