from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Literal

import google.auth
import google.auth.transport.requests
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


BlockReason = Literal["injection", "toxicity", "url", "sensitive_data", "none"]

_BLOCKING_CONFIDENCES = {"MEDIUM", "MEDIUM_HIGH", "MEDIUM_AND_ABOVE", "HIGH"}
_REQUEST_TIMEOUT_SECONDS = 3.0


@dataclass(slots=True, frozen=True)
class SanitizationResult:
    blocked: bool
    reason: BlockReason
    detail: str = ""


_SAFE_RESULT = SanitizationResult(blocked=False, reason="none")


async def sanitize_user_prompt(text: str) -> SanitizationResult:
    if not settings.MODEL_ARMOR_ENABLED:
        return _SAFE_RESULT
    if not settings.MODEL_ARMOR_TEMPLATE_ID:
        logger.error(
            "model_armor_misconfigured",
            extra={"reason": "MODEL_ARMOR_ENABLED=True pero MODEL_ARMOR_TEMPLATE_ID está vacío"},
        )
        return _SAFE_RESULT
    if not text:
        return _SAFE_RESULT

    try:
        response = await asyncio.to_thread(_call_sanitize_endpoint, text)
    except httpx.HTTPStatusError as exc:
        if 400 <= exc.response.status_code < 500:
            logger.error(
                "model_armor_misconfigured",
                extra={
                    "status_code": exc.response.status_code,
                    "body": exc.response.text[:500],
                    "hint": "Revisa MODEL_ARMOR_TEMPLATE_ID, permisos IAM (roles/modelarmor.user) y región.",
                },
            )
        else:
            logger.warning("model_armor_upstream_error", extra={"status_code": exc.response.status_code})
        return _SAFE_RESULT
    except Exception:
        logger.warning("model_armor_call_failed", exc_info=True)
        return _SAFE_RESULT

    return _interpret_response(response)


_credentials_cache: Any = None
_http_client: httpx.Client | None = None


def _get_credentials_token() -> str:
    global _credentials_cache
    if _credentials_cache is None:
        _credentials_cache, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    if not _credentials_cache.valid:
        _credentials_cache.refresh(google.auth.transport.requests.Request())
    return _credentials_cache.token


def _get_http_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=_REQUEST_TIMEOUT_SECONDS)
    return _http_client


def _call_sanitize_endpoint(text: str) -> dict[str, Any]:
    project_id = settings.GOOGLE_CLOUD_PROJECT or settings.BIGQUERY_PROJECT_ID
    if not project_id:
        raise RuntimeError("Falta GOOGLE_CLOUD_PROJECT para Model Armor")

    location = settings.MODEL_ARMOR_LOCATION
    template = settings.MODEL_ARMOR_TEMPLATE_ID
    url = (
        f"https://modelarmor.{location}.rep.googleapis.com/v1/"
        f"projects/{project_id}/locations/{location}/templates/{template}:sanitizeUserPrompt"
    )

    headers = {
        "Authorization": f"Bearer {_get_credentials_token()}",
        "Content-Type": "application/json",
    }
    payload = {"user_prompt_data": {"text": text}}

    resp = _get_http_client().post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()


def _interpret_response(response: dict[str, Any]) -> SanitizationResult:
    sanitization = response.get("sanitizationResult", {})
    if sanitization.get("filterMatchState") != "MATCH_FOUND":
        return _SAFE_RESULT

    filter_results = sanitization.get("filterResults", {})
    for raw_filter, payload in filter_results.items():
        result = _extract_filter_match(raw_filter, payload)
        if result.blocked:
            return result
    return _SAFE_RESULT


def _extract_filter_match(filter_key: str, payload: dict[str, Any]) -> SanitizationResult:
    inner = next(iter(payload.values())) if isinstance(payload, dict) and payload else {}
    if not isinstance(inner, dict):
        return _SAFE_RESULT
    if inner.get("matchState") != "MATCH_FOUND":
        return _SAFE_RESULT

    confidence = inner.get("confidenceLevel", "")
    if confidence not in _BLOCKING_CONFIDENCES:
        return _SAFE_RESULT

    reason = _map_filter_to_reason(filter_key)
    return SanitizationResult(blocked=True, reason=reason, detail=confidence)


def _map_filter_to_reason(filter_key: str) -> BlockReason:
    key = filter_key.lower()
    if "pi" in key or "jailbreak" in key or "prompt" in key:
        return "injection"
    if "rai" in key or "toxic" in key or "harm" in key:
        return "toxicity"
    if "url" in key or "malicious" in key:
        return "url"
    if "sdp" in key or "sensitive" in key:
        return "sensitive_data"
    return "injection"
