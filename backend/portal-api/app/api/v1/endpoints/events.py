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
    limit: int = Query(50, le=200),
) -> list[EventRead]:
    db = get_firestore()
    query = db.collection(COLLECTION)
    if ciudad:
        query = query.where("ciudad", "==", ciudad)
    if segmento:
        query = query.where("segmento", "==", segmento)
    query = query.order_by("fecha_utc").limit(limit)
    docs = await query.get()
    return [_doc_to_event(doc.id, doc.to_dict()) for doc in docs]


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: str) -> EventRead:
    db = get_firestore()
    doc = await db.collection(COLLECTION).document(event_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return _doc_to_event(doc.id, doc.to_dict())
