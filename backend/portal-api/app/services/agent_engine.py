from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any

import vertexai
from vertexai import agent_engines

from app.config import settings

logger = logging.getLogger(__name__)


_AGENT_TIMEOUT_SECONDS = 60.0


class AgentEngineError(RuntimeError):
    pass


def _event_text(event: Any) -> str:
    if isinstance(event, str):
        return event
    if isinstance(event, dict):
        if isinstance(event.get("text"), str):
            return event["text"]
        content = event.get("content") or {}
        parts = content.get("parts") if isinstance(content, dict) else None
        if parts:
            return "\n".join(str(p.get("text", "")) for p in parts if isinstance(p, dict)).strip()
    text = getattr(event, "text", None)
    return text if isinstance(text, str) else ""


@lru_cache(maxsize=1)
def _get_remote_agent() -> Any:
    if not settings.AGENT_ENGINE_RESOURCE_NAME:
        raise AgentEngineError("AGENT_ENGINE_RESOURCE_NAME no está configurado")

    project_id = settings.GOOGLE_CLOUD_PROJECT or settings.BIGQUERY_PROJECT_ID or None
    vertexai.init(project=project_id, location=settings.AGENT_REGION)
    return agent_engines.get(settings.AGENT_ENGINE_RESOURCE_NAME)


async def ask_agent(*, user_id: str, session_id: str, message: str) -> str:
    remote_agent = _get_remote_agent()

    try:
        await asyncio.to_thread(remote_agent.create_session, user_id=user_id, session_id=session_id)
    except Exception:
        logger.debug("agent_session_create_skipped", exc_info=True)

    def _do_stream() -> list[str]:
        result: list[str] = []
        try:
            events = remote_agent.stream_query(
                user_id=user_id,
                session_id=session_id,
                message=message,
            )
        except TypeError:
            events = remote_agent.stream_query(user_id=user_id, message=message)
        for event in events:
            text = _event_text(event)
            if text:
                result.append(text)
        return result

    try:
        chunks = await asyncio.wait_for(
            asyncio.to_thread(_do_stream),
            timeout=_AGENT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise AgentEngineError(
            f"El agente no respondió en {_AGENT_TIMEOUT_SECONDS:.0f}s"
        ) from exc

    answer = "\n".join(chunk for chunk in chunks if chunk).strip()
    if not answer:
        raise AgentEngineError("El agente no devolvió respuesta")
    return answer
