from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.db.firestore import get_firestore
from app.schemas.event import EventRead

router = APIRouter(prefix="/events", tags=["events"])

COLLECTION = "eventos"


def _coerce(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _coerce(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce(v) for v in value]
    return value


def _doc_to_event(doc_id: str, data: dict) -> EventRead:
    # Firestore documents may carry an `id` field (ingestion pipeline writes it
    # alongside the doc key); `doc_id` from the document path is authoritative.
    data.pop("id", None)
    return EventRead(id=doc_id, **_coerce(data))


async def _run_query(
    limit: int,
    ciudad: str | None = None,
    segmento: list[str] | None = None,
    fecha: str | None = None,
) -> list[EventRead]:
    db = get_firestore()
    q = db.collection(COLLECTION)
    if ciudad:
        q = q.where("ciudad", "==", ciudad)
    if fecha:
        q = q.where("fecha", "==", fecha)
    if segmento:
        if len(segmento) == 1:
            q = q.where("segmento", "==", segmento[0])
        else:
            q = q.where("segmento", "in", segmento[:10])
    q = q.order_by("fecha_utc").limit(limit)
    docs = await q.get()
    return [_doc_to_event(doc.id, doc.to_dict()) for doc in docs]


@router.get("", response_model=list[EventRead])
async def list_events(
    ciudad: str | None = None,
    segmento: list[str] | None = Query(None),
    fecha: str | None = None,
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lng: float | None = None,
    max_lng: float | None = None,
    limit: int | None = Query(1000, ge=1, le=5000),
) -> list[EventRead]:
    items = await _run_query(limit or 1000, ciudad=ciudad, segmento=segmento, fecha=fecha)

    bbox = all(v is not None for v in (min_lat, max_lat, min_lng, max_lng))
    if not bbox:
        return items

    filtered = []
    for e in items:
        if e.latitud is None or e.longitud is None:
            continue
        if not (min_lat <= e.latitud <= max_lat):
            continue
        if not (min_lng <= e.longitud <= max_lng):
            continue
        filtered.append(e)
    return filtered


@router.get("/categories", response_model=list[str])
async def list_categories(
    ciudad: str | None = None,
    fecha: str | None = None,
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lng: float | None = None,
    max_lng: float | None = None,
) -> list[str]:
    items = await _run_query(5000, ciudad=ciudad, fecha=fecha)

    bbox = all(v is not None for v in (min_lat, max_lat, min_lng, max_lng))
    segmentos: set[str] = set()
    for e in items:
        if bbox:
            if e.latitud is None or e.longitud is None:
                continue
            if not (min_lat <= e.latitud <= max_lat):
                continue
            if not (min_lng <= e.longitud <= max_lng):
                continue
        if e.segmento:
            segmentos.add(e.segmento)
    return sorted(segmentos)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: str) -> EventRead:
    db = get_firestore()
    doc = await db.collection(COLLECTION).document(event_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return _doc_to_event(doc.id, doc.to_dict())
