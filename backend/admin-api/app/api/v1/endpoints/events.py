from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.dependencies import get_admin_user
from app.db.firestore import get_firestore
from app.models.user import User

router = APIRouter(prefix="/events", tags=["events"])

COLLECTION = "eventos"

_ADMIN_EVENT_FIELDS = [
    "nombre", "ciudad", "segmento", "fecha", "hora",
    "recinto_nombre", "estado",
]


class EventAdminRead(BaseModel):
    id: str
    nombre: str | None = None
    ciudad: str | None = None
    segmento: str | None = None
    fecha: str | None = None
    hora: str | None = None
    recinto_nombre: str | None = None
    estado: str | None = None


def _coerce(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _coerce(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce(v) for v in value]
    return value


@router.get("", response_model=list[EventAdminRead])
async def list_events(
    limit: int = Query(100, ge=1, le=1000),
    ciudad: str | None = None,
    segmento: str | None = None,
    _: User = Depends(get_admin_user),
) -> list[EventAdminRead]:
    db = get_firestore()
    q = db.collection(COLLECTION).select(_ADMIN_EVENT_FIELDS)
    if ciudad:
        q = q.where("ciudad", "==", ciudad)
    if segmento:
        q = q.where("segmento", "==", segmento)
    q = q.order_by("fecha_utc").limit(limit)
    docs = await q.get()

    results = []
    for doc in docs:
        data = _coerce(doc.to_dict())
        results.append(EventAdminRead(
            id=doc.id,
            nombre=data.get("nombre"),
            ciudad=data.get("ciudad"),
            segmento=data.get("segmento"),
            fecha=data.get("fecha"),
            hora=data.get("hora"),
            recinto_nombre=data.get("recinto_nombre"),
            estado=data.get("estado"),
        ))
    return results
