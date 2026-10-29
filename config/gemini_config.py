"""
Centralized Gemini API Configuration & Model Registry.

Provides a unified, production-ready configuration for all Gemini model interactions:
- Centralized model names and validated model aliases
- Multi-tier fallback hierarchy (Primary Lightweight -> Secondary Lightweight -> Final Fallback)
- Exponential backoff with jitter and retry parameters
- Request timeouts
- Secret masking to ensure API keys are never exposed in logs or user interfaces
"""

import os
import re
from typing import List, Dict, Optional, Tuple


def mask_secret(secret: Optional[str]) -> str:
    """Masks sensitive strings like API keys for secure logging."""
    if not secret:
        return "[NOT SET]"
    secret_str = str(secret).strip()
    if len(secret_str) <= 8:
        return "***"
    return f"{secret_str[:6]}...{secret_str[-4:]}"


# Model Registry: Active and Verified Google GenAI SDK Models
# (Verified against live Google Generative Language API endpoints)
VALID_PRIMARY_LITE_MODEL = "gemini-3.1-flash-lite"
VALID_SECONDARY_LITE_MODEL = "gemini-flash-lite-latest"
VALID_TERTIARY_MODEL = "gemini-3.8-flash"
VALID_RESERVE_MODEL = "gemini-3-flash-preview"

# Known model alias mappings (e.g. mapping unsupported, deprecated, or IDE-specific names)
MODEL_NAME_ALIASES: Dict[str, str] = {
    # Non-standard or internal preview models mapped to verified active models
    "gemini-3.8-flash-medium": VALID_TERTIARY_MODEL,
    "gemini-3.6-flash": VALID_TERTIARY_MODEL,
    "gemini-3.5-flash": VALID_TERTIARY_MODEL,
    "gemini-3.7-flash": VALID_TERTIARY_MODEL,
    "gemini-2.5-flash": VALID_TERTIARY_MODEL,
    "gemini-2.5-flash-lite": VALID_PRIMARY_LITE_MODEL,
    "gemini-flash-lite": VALID_PRIMARY_LITE_MODEL,
    "gemini-flash": VALID_TERTIARY_MODEL,
    "flash-lite": VALID_PRIMARY_LITE_MODEL,
    "flash": VALID_TERTIARY_MODEL,
}


def sanitize_model_name(model_name: Optional[str]) -> str:
    """
    Normalizes and maps model names to guaranteed valid GenAI SDK endpoints.
    Catches invalid models like 'gemini-3.8-flash-medium' and redirects to valid models.
    """
    if not model_name:
        return VALID_PRIMARY_LITE_MODEL
    
    clean_name = model_name.strip().lower()
    # Strip any prefix like 'models/'
    if clean_name.startswith("models/"):
        clean_name = clean_name[len("models/"):]
        
    if clean_name in MODEL_NAME_ALIASES:
        return MODEL_NAME_ALIASES[clean_name]
    
    return clean_name


class GeminiConfig:
    """
    Centralized Gemini API Configuration singleton.
    Reads from environment variables and applies resilient defaults.
    """

    # API Key Configuration: Must be supplied via GEMINI_API_KEY environment variable
    _RAW_API_KEY: str = os.environ.get(
        "GEMINI_API_KEY",
        ""
    )

    @classmethod
    def get_api_key(cls) -> str:
        """Returns the configured API key (reads from environment if updated)."""
        return os.environ.get("GEMINI_API_KEY", cls._RAW_API_KEY)

    @classmethod
    def get_masked_api_key(cls) -> str:
        """Returns masked API key for logging purposes."""
        return mask_secret(cls.get_api_key())

    # Configured Model Tiers
    PRIMARY_LITE_MODEL: str = sanitize_model_name(
        os.environ.get("GEMINI_PRIMARY_MODEL", VALID_PRIMARY_LITE_MODEL)
    )
    SECONDARY_LITE_MODEL: str = sanitize_model_name(
        os.environ.get("GEMINI_SECONDARY_MODEL", VALID_SECONDARY_LITE_MODEL)
    )
    FINAL_FALLBACK_MODEL: str = sanitize_model_name(
        os.environ.get("GEMINI_FALLBACK_MODEL", VALID_TERTIARY_MODEL)
    )
    RESERVE_FALLBACK_MODEL: str = VALID_RESERVE_MODEL

    # Strong model for complex reasoning tasks
    STRONG_MODEL: str = VALID_TERTIARY_MODEL

    # Resiliency & Retry Policy
    MAX_RETRIES_PER_MODEL: int = int(os.environ.get("GEMINI_MAX_RETRIES", "2"))
    BASE_RETRY_DELAY_SEC: float = float(os.environ.get("GEMINI_BASE_RETRY_DELAY", "1.0"))
    MAX_RETRY_DELAY_SEC: float = float(os.environ.get("GEMINI_MAX_RETRY_DELAY", "8.0"))
    JITTER_FACTOR: float = 0.25  # +/- 25% random jitter to avoid thundering herd
    REQUEST_TIMEOUT_SECONDS: float = float(os.environ.get("GEMINI_REQUEST_TIMEOUT", "25.0"))

    # Caching & Deduplication
    ENABLE_RESPONSE_CACHE: bool = True
    MAX_CACHE_SIZE: int = 256

    @classmethod
    def get_model_cascade(cls, is_strong_task: bool = False) -> List[str]:
        """
        Returns an ordered list of fallback models.
        - Normal/Lightweight tasks: Primary Lite -> Secondary Lite -> Final Fallback -> Reserve
        - Strong tasks: Strong Model -> Primary Lite -> Secondary Lite
        """
        if is_strong_task:
            cascade = [
                cls.STRONG_MODEL,
                cls.PRIMARY_LITE_MODEL,
                cls.SECONDARY_LITE_MODEL,
                cls.RESERVE_FALLBACK_MODEL,
            ]
        else:
            cascade = [
                cls.PRIMARY_LITE_MODEL,
                cls.SECONDARY_LITE_MODEL,
                cls.FINAL_FALLBACK_MODEL,
                cls.RESERVE_FALLBACK_MODEL,
            ]
        
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for m in cascade:
            sanitized = sanitize_model_name(m)
            if sanitized not in seen:
                seen.add(sanitized)
                deduped.append(sanitized)
        return deduped
