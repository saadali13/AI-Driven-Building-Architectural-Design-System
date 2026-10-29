"""
Test Suite for Resilient Gemini Service Layer.

Verifies:
1. Live Gemini API execution with primary lightweight model (gemini-3.1-flash-lite).
2. Simulated HTTP 503 UNAVAILABLE with exponential backoff and jitter.
3. Simulated automatic fallback from primary to secondary/tertiary models when primary is unavailable.
4. Simulated 429 RESOURCE_EXHAUSTED handling.
5. Simulated request timeout handling.
6. Request deduplication / response caching.
7. Sanitization of invalid model names (e.g. gemini-3.8-flash-medium).
8. Masking of API secrets (no API key leaks in logs/errors).
9. Rule-based architectural fallback when all upstream models are unavailable.
"""

import os
import time
import pytest
from unittest.mock import MagicMock, patch

from config.gemini_config import (
    GeminiConfig,
    sanitize_model_name,
    mask_secret,
    VALID_PRIMARY_LITE_MODEL,
    VALID_SECONDARY_LITE_MODEL,
    VALID_TERTIARY_MODEL,
)
from generation.gemini_service import (
    GeminiService,
    GeminiServiceUnavailableError,
    get_gemini_service,
)
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    RoomModel,
)
from generation.gemini_architectural_auditor import GeminiArchitecturalAuditor


def test_model_name_sanitizer():
    """Verify that unsupported/IDE-specific model names are safely redirected."""
    assert sanitize_model_name("gemini-3.8-flash-medium") == VALID_TERTIARY_MODEL
    assert sanitize_model_name("models/gemini-3.8-flash-medium") == VALID_TERTIARY_MODEL
    assert sanitize_model_name("gemini-3.6-flash") == VALID_TERTIARY_MODEL
    assert sanitize_model_name("gemini-2.5-flash-lite") == VALID_PRIMARY_LITE_MODEL
    assert sanitize_model_name("gemini-3.1-flash-lite") == "gemini-3.1-flash-lite"
    assert sanitize_model_name(None) == VALID_PRIMARY_LITE_MODEL


def test_api_key_masking():
    """Verify secrets are masked to prevent leakages."""
    dummy_key = "MOCK_KEY_SECRET_FOR_UNIT_TEST_SAMPLE_987654321"
    masked = mask_secret(dummy_key)
    assert "MOCK_K" in masked
    assert "4321" in masked
    assert "SECRET_FOR_UNIT_TEST" not in masked
    assert mask_secret("") == "[NOT SET]"
    assert mask_secret(None) == "[NOT SET]"


def test_live_gemini_primary_lite_model():
    """Test live request with primary fast/lightweight model."""
    service = GeminiService()
    prompt = "Return valid JSON with key 'greeting': {\"greeting\": \"hello\"}"
    result = service.generate_json(prompt, is_strong_task=False)
    assert isinstance(result, dict)
    assert "greeting" in result
    assert result["greeting"].lower() == "hello"


def test_request_deduplication_cache():
    """Verify that identical requests hit the cache and do not make duplicate network calls."""
    service = GeminiService()
    prompt = "Deduplication cache test unique string 12345"

    with patch.object(service._get_client().models, "generate_content") as mock_gen:
        mock_response = MagicMock()
        mock_response.text = '{"cached": true}'
        mock_gen.return_value = mock_response

        res1 = service.generate_content(prompt, bypass_cache=False)
        assert res1 == '{"cached": true}'
        assert mock_gen.call_count == 1

        # Second call with same prompt should be served from memory cache
        res2 = service.generate_content(prompt, bypass_cache=False)
        assert res2 == '{"cached": true}'
        assert mock_gen.call_count == 1, "Duplicate network call was made instead of using cache!"


def test_simulated_503_backoff_and_retry_success():
    """Simulate temporary 503 UNAVAILABLE on attempt 1, followed by success on attempt 2."""
    service = GeminiService()
    call_counts = {"count": 0}

    def fake_generate_content(model, contents):
        call_counts["count"] += 1
        if call_counts["count"] == 1:
            raise Exception("503 UNAVAILABLE: High demand temporary server spike")
        mock_res = MagicMock()
        mock_res.text = "Success after backoff"
        return mock_res

    with patch.object(service._get_client().models, "generate_content", side_effect=fake_generate_content):
        start_time = time.time()
        result = service.generate_content("test prompt", bypass_cache=True)
        elapsed = time.time() - start_time

        assert result == "Success after backoff"
        assert call_counts["count"] == 2
        # Backoff should have introduced a delay >= 0.2s
        assert elapsed >= 0.2


def test_simulated_fallback_to_secondary_model():
    """Simulate primary model being completely 503 unavailable, falling back to secondary model."""
    service = GeminiService()
    attempted_models = []

    cascade = GeminiConfig.get_model_cascade(is_strong_task=False)
    primary = cascade[0]
    secondary = cascade[1]

    def fake_generate_content(model, contents):
        attempted_models.append(model)
        if model == primary:
            raise Exception("503 UNAVAILABLE: No capacity available on primary model")
        mock_res = MagicMock()
        mock_res.text = f"Recovered from fallback model: {model}"
        return mock_res

    with patch.object(service._get_client().models, "generate_content", side_effect=fake_generate_content):
        result = service.generate_content("fallback test prompt", bypass_cache=True)

        assert f"Recovered from fallback model: {secondary}" in result
        # Primary was retried MAX_RETRIES_PER_MODEL times
        assert attempted_models.count(primary) == GeminiConfig.MAX_RETRIES_PER_MODEL
        # Secondary succeeded on first attempt
        assert attempted_models.count(secondary) == 1


def test_simulated_429_resource_exhausted_fallback():
    """Simulate 429 RESOURCE_EXHAUSTED rate limit on primary model, falling back to secondary."""
    service = GeminiService()
    attempted_models = []

    cascade = GeminiConfig.get_model_cascade(is_strong_task=False)
    primary = cascade[0]
    secondary = cascade[1]

    def fake_generate_content(model, contents):
        attempted_models.append(model)
        if model == primary:
            raise Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded")
        mock_res = MagicMock()
        mock_res.text = "Success on secondary"
        return mock_res

    with patch.object(service._get_client().models, "generate_content", side_effect=fake_generate_content):
        result = service.generate_content("rate limit test", bypass_cache=True)
        assert result == "Success on secondary"
        assert attempted_models.count(primary) == GeminiConfig.MAX_RETRIES_PER_MODEL
        assert secondary in attempted_models


def test_simulated_all_models_unavailable_raises_clean_error():
    """Simulate all models in cascade failing, verifying application-level error without leaking secrets."""
    service = GeminiService()

    def fake_generate_content(model, contents):
        raise Exception("503 UNAVAILABLE: Total service disruption")

    with patch.object(service._get_client().models, "generate_content", side_effect=fake_generate_content):
        with pytest.raises(GeminiServiceUnavailableError) as exc_info:
            service.generate_content("test all fail", bypass_cache=True)

        err_msg = str(exc_info.value)
        assert "temporarily unavailable" in err_msg
        # Raw API key must not be present in exception string
        assert GeminiConfig.get_api_key() not in err_msg


def test_simulated_request_timeout_fallback():
    """Verify that a timeout on primary model falls back to secondary model."""
    from concurrent.futures import TimeoutError as FutureTimeoutError
    service = GeminiService()
    cascade = GeminiConfig.get_model_cascade(is_strong_task=False)
    primary = cascade[0]
    secondary = cascade[1]

    attempted_models = []

    def fake_generate_content(model, contents):
        attempted_models.append(model)
        if model == primary:
            raise FutureTimeoutError("Call timed out after 25s")
        mock_res = MagicMock()
        mock_res.text = "Timeout recovery success"
        return mock_res

    with patch.object(service._get_client().models, "generate_content", side_effect=fake_generate_content):
        result = service.generate_content("timeout prompt", bypass_cache=True)
        assert result == "Timeout recovery success"
        assert secondary in attempted_models


def test_auditor_deterministic_fallback_when_service_down():
    """Verify that GeminiArchitecturalAuditor gracefully falls back to rule-based auditor when service is down."""
    metadata = MetadataModel(
        plan_id="test_plan",
        source_type="synthetic_generated",
        floor_count=2,
        provenance={"scale": "7_marla"}
    )
    room = RoomModel(
        room_id="r1",
        room_name="Front Lawn",
        room_type="outdoor",
        polygon=[[0, 0], [10, 0], [10, 3], [0, 3]],
        area_m2=30.0,
        centroid=[5.0, 1.5],
        level_index=0,
        is_habitable=False,
    )
    plan = CanonicalFloorPlan(
        metadata=metadata,
        boundary=[[0, 0], [10, 0], [10, 18], [0, 18]],
        total_area_m2=180.0,
        rooms=[room],
        walls=[],
        openings=[]
    )

    with patch.object(GeminiService, "generate_json", side_effect=GeminiServiceUnavailableError("Down")):
        audited_plan, audit_result = GeminiArchitecturalAuditor.audit_and_refine(
            plan=plan,
            user_prompt="Build a 7 Marla Spanish Revival house"
        )
        assert audit_result["status"] == "APPROVED"
        assert "Verified layout compliance" in audit_result["senior_architect_verdict"]
        # Lawn must not be altered
        assert audited_plan.rooms[0].room_type == "outdoor"

