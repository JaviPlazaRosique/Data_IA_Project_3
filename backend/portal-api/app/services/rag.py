from __future__ import annotations

import re
from datetime import date, timedelta

from app.db.firestore import get_firestore
from app.schemas.event import EventRead

_CITY_KEYWORDS: dict[str, str] = {
    "madrid": "madrid",
    "barcelona": "barcelona",
    "valencia": "valencia",
    "sevilla": "sevilla",
    "seville": "sevilla",
    "bilbao": "bilbao",
    "málaga": "malaga",
    "malaga": "malaga",
    "zaragoza": "zaragoza",
    "mallorca": "mallorca",
    "palma": "mallorca",
}

_SEGMENT_KEYWORDS: dict[str, str] = {
    "música": "Music",
    "musica": "Music",
    "music": "Music",
    "concierto": "Music",
    "festival": "Music",
    "rock": "Music",
    "pop": "Music",
    "electrónica": "Music",
    "electronica": "Music",
    "reggaeton": "Music",
    "rap": "Music",
    "jazz": "Music",
    "fútbol": "Sports",
    "futbol": "Sports",
    "deporte": "Sports",
    "partido": "Sports",
    "tenis": "Sports",
    "baloncesto": "Sports",
    "sports": "Sports",
    "teatro": "Arts & Theatre",
    "musical": "Arts & Theatre",
    "danza": "Arts & Theatre",
    "exposición": "Arts & Theatre",
    "exposicion": "Arts & Theatre",
    "arte": "Arts & Theatre",
    "cine": "Arts & Theatre",
    "familia": "Family",
    "niños": "Family",
    "ninos": "Family",
    "circo": "Family",
    "kids": "Family",
}

_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def _extract_hints(query: str) -> dict:
    q = query.lower()
    hints: dict = {}

    for kw, city in _CITY_KEYWORDS.items():
        if kw in q:
            hints["ciudad"] = city
            break

    for kw, seg in _SEGMENT_KEYWORDS.items():
        if kw in q:
            hints["segmento"] = seg
            break

    today = date.today()
    if "hoy" in q or "today" in q:
        hints["fecha"] = today.isoformat()
    elif "mañana" in q or "manana" in q or "tomorrow" in q:
        hints["fecha"] = (today + timedelta(days=1)).isoformat()
    elif "finde" in q or "fin de semana" in q or "weekend" in q:
        days_until_saturday = (5 - today.weekday()) % 7 or 7
        hints["fecha"] = (today + timedelta(days=days_until_saturday)).isoformat()
    else:
        m = _DATE_PATTERN.search(query)
        if m:
            hints["fecha"] = m.group(1)

    return hints


def _coerce(value):
    from datetime import datetime
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _coerce(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce(v) for v in value]
    return value


async def _query_firestore_events(hints: dict, limit: int) -> list[EventRead]:
    db = get_firestore()
    q = db.collection("eventos")
    if hints.get("ciudad"):
        q = q.where("ciudad", "==", hints["ciudad"])
    if hints.get("fecha"):
        q = q.where("fecha", "==", hints["fecha"])
    if hints.get("segmento"):
        q = q.where("segmento", "==", hints["segmento"])
    q = q.order_by("fecha_utc").limit(limit)
    docs = await q.get()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data.pop("id", None)
        results.append(EventRead(id=doc.id, **_coerce(data)))
    return results


async def retrieve_events_for_query(query: str, limit: int = 8) -> list[EventRead]:
    hints = _extract_hints(query)
    try:
        events = await _query_firestore_events(hints, limit)
        if events:
            return events
        # Fallback: remove date constraint and retry
        hints.pop("fecha", None)
        if hints:
            events = await _query_firestore_events(hints, limit)
        return events
    except Exception:
        return []
