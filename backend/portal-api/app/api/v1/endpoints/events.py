from fastapi import APIRouter, HTTPException, Query, status

from app.db.firestore import get_firestore
from app.schemas.event import EventRead

router = APIRouter(prefix="/events", tags=["events"])

COLLECTION = "eventos"


def _doc_to_event(doc_id: str, data: dict) -> EventRead:
    # Firestore documents may carry an `id` field (ingestion pipeline writes it
    # alongside the doc key); `doc_id` from the document path is authoritative.
    data.pop("id", None)
    return EventRead(id=doc_id, **data)


@router.get("", response_model=list[EventRead])
async def list_events(
    ciudad: str | None = None,
    segmento: str | None = None,
    fecha: str | None = None,
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lng: float | None = None,
    max_lng: float | None = None,
    limit: int | None = Query(None, ge=1),
) -> list[EventRead]:
    db = get_firestore()
    query = db.collection(COLLECTION)
    if ciudad:
        query = query.where("ciudad", "==", ciudad)
    if segmento:
        query = query.where("segmento", "==", segmento)
    if fecha:
        query = query.where("fecha", "==", fecha)

    bbox = all(v is not None for v in (min_lat, max_lat, min_lng, max_lng))
    if bbox:
        # Firestore allows a range inequality on only one field per query, so
        # we constrain latitude server-side and filter longitude in Python.
        query = (
            query.where("latitud", ">=", min_lat)
            .where("latitud", "<=", max_lat)
            .order_by("latitud")
        )
        if limit is not None:
            query = query.limit(limit * 3)
    else:
        effective_limit = limit if limit is not None else 50
        query = query.order_by("fecha_utc").limit(effective_limit)

    docs = await query.get()
    items = [_doc_to_event(doc.id, doc.to_dict()) for doc in docs]
    if bbox:
        items = [
            e for e in items
            if e.longitud is not None and min_lng <= e.longitud <= max_lng
        ]
        if limit is not None:
            items = items[:limit]
    return items


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: str) -> EventRead:
    db = get_firestore()
    doc = await db.collection(COLLECTION).document(event_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return _doc_to_event(doc.id, doc.to_dict())
