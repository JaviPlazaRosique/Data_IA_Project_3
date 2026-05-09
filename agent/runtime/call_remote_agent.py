from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

import vertexai
from vertexai import agent_engines


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


async def call_remote(resource_name: str, user_id: str, session_id: str, message: str) -> None:
    vertexai.init(project=os.getenv("PROJECT_ID") or None, location=os.getenv("REGION", "europe-west1"))
    remote_agent = agent_engines.get(resource_name)
    try:
        remote_agent.create_session(user_id=user_id, session_id=session_id)
    except Exception:
        pass
    try:
        stream = remote_agent.async_stream_query(user_id=user_id, session_id=session_id, message=message)
    except TypeError:
        stream = remote_agent.async_stream_query(user_id=user_id, message=message)
    async for event in stream:
        text = _event_text(event)
        if text:
            print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Llama a un Agent Engine desplegado")
    parser.add_argument("--resource-name", default=os.getenv("AGENT_ENGINE_RESOURCE_NAME", ""))
    parser.add_argument("--user-id",       default=os.getenv("USER_ID", "demo-user"))
    parser.add_argument("--session-id",    default=os.getenv("SESSION_ID", "session-001"))
    parser.add_argument("--message",       default="¿Qué puedo hacer un viernes por la noche?")
    args = parser.parse_args()
    if not args.resource_name:
        raise SystemExit("Falta --resource-name o $AGENT_ENGINE_RESOURCE_NAME")
    asyncio.run(call_remote(args.resource_name, args.user_id, args.session_id, args.message))


if __name__ == "__main__":
    main()
