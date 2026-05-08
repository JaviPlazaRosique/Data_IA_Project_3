from __future__ import annotations

import asyncio
from functools import lru_cache

import vertexai
from vertexai.generative_models import Content, GenerativeModel, Part

from app.config import settings
from app.schemas.event import EventRead
from app.schemas.plan import PlanMessage
from app.schemas.recommendation import ClusterRecommendationRead
from app.services.user_profile import UserTasteProfile

_SYSTEM_PROMPT = """Eres un asistente de planificación cultural para España.
Ayudas al usuario a planificar salidas de ocio — conciertos, festivales, teatro, deportes y eventos culturales.

Reglas:
- Responde siempre en español.
- Sé entusiasta pero conciso: máximo 3-4 párrafos por respuesta.
- Usa el perfil de gustos y los eventos recomendados para personalizar tus sugerencias.
- Cuando dispongas de eventos del catálogo relevantes a la consulta, cítalos con nombre, fecha y ciudad.
- Si no tienes datos de un evento específico, dilo con honestidad.
- No inventes precios ni horarios.
- Cuando sea útil, sugiere cómo combinar eventos en un mismo día o fin de semana.
"""

_HISTORY_WINDOW = 20


@lru_cache(maxsize=1)
def _get_model() -> GenerativeModel:
    vertexai.init(
        project=settings.GOOGLE_CLOUD_PROJECT,
        location=settings.GEMINI_LOCATION,
    )
    return GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=_SYSTEM_PROMPT,
    )


def _to_vertex_history(messages: list[PlanMessage]) -> list[Content]:
    """Convert prior messages to Vertex AI history, capped at _HISTORY_WINDOW."""
    prior = messages[:-1][-_HISTORY_WINDOW:]
    history: list[Content] = []
    for msg in prior:
        role = "user" if msg.role == "user" else "model"
        history.append(Content(role=role, parts=[Part.from_text(msg.content)]))
    return history


def _recommendations_context(recs: list[ClusterRecommendationRead]) -> str:
    if not recs:
        return ""
    lines = ["[Eventos recomendados para este usuario]"]
    for rec in recs[:10]:
        name = rec.event_name or rec.event_id
        date = rec.fecha_evento or "?"
        city = rec.ciudad or "?"
        genre = " / ".join(filter(None, [rec.segmento, rec.genero, rec.subgenero]))
        lines.append(f"• {name} — {date}, {city}" + (f" ({genre})" if genre else ""))
    return "\n".join(lines)


def _rag_events_context(events: list[EventRead]) -> str:
    if not events:
        return ""
    lines = ["[Eventos del catálogo relevantes a tu consulta]"]
    for ev in events:
        name = ev.nombre or ev.id
        date = ev.fecha or "?"
        city = ev.ciudad or "?"
        genre = " / ".join(filter(None, [ev.segmento, ev.genero, ev.subgenero]))
        venue = ev.recinto_nombre or ""
        line = f"• {name} — {date}, {city}"
        if venue:
            line += f" ({venue})"
        if genre:
            line += f" [{genre}]"
        lines.append(line)
    return "\n".join(lines)


def _build_context_block(
    recommendations: list[ClusterRecommendationRead],
    user_profile: UserTasteProfile | None,
    rag_events: list[EventRead] | None = None,
) -> str:
    parts: list[str] = []
    if user_profile:
        parts.append(user_profile.to_context_string())
    rec_ctx = _recommendations_context(recommendations)
    if rec_ctx:
        parts.append(rec_ctx)
    rag_ctx = _rag_events_context(rag_events or [])
    if rag_ctx:
        parts.append(rag_ctx)
    return "\n\n".join(parts)


async def generate_chat_reply(
    messages: list[PlanMessage],
    recommendations: list[ClusterRecommendationRead],
    user_profile: UserTasteProfile | None = None,
    rag_events: list[EventRead] | None = None,
) -> str:
    if not messages:
        raise ValueError("messages list is empty")

    model = _get_model()
    history = _to_vertex_history(messages)
    last_content = messages[-1].content

    # Always prepend context block so it survives history windowing
    ctx = _build_context_block(recommendations, user_profile, rag_events)
    user_turn = f"{ctx}\n\n{last_content}" if ctx else last_content

    def _call() -> str:
        chat = model.start_chat(history=history)
        return chat.send_message(user_turn).text

    return await asyncio.to_thread(_call)
