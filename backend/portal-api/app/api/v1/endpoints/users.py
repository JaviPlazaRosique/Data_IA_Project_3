import logging

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from google.cloud import storage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.firestore import get_firestore
from app.dependencies import get_current_user, get_db
from app.models.saved_event import SavedEvent
from app.models.user import User
from app.schemas.saved_event import SavedEventRead
from app.schemas.user import UserRead, UserUpdate

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_HEADERS = {"User-Agent": "NextPlan-Portal/1.0 (j.plazarosique@gmail.com)"}


async def _geocode(location: str) -> tuple[float, float] | None:
    """Return (lat, lng) for a location string using Nominatim, or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                _NOMINATIM_URL,
                params={"q": location, "format": "json", "limit": 1},
                headers=_NOMINATIM_HEADERS,
            )
            r.raise_for_status()
            results = r.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        logger.warning("Geocoding failed for location=%r", location)
    return None

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    update_data = body.model_dump(exclude_unset=True)

    if "preferred_location" in update_data:
        location = update_data["preferred_location"]
        if location:
            coords = await _geocode(location)
            if coords:
                update_data["preferred_location_lat"] = coords[0]
                update_data["preferred_location_lng"] = coords[1]
            else:
                update_data["preferred_location_lat"] = None
                update_data["preferred_location_lng"] = None
        else:
            update_data["preferred_location_lat"] = None
            update_data["preferred_location_lng"] = None

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    request: Request,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato no admitido. Usa JPEG, PNG, WEBP o GIF.",
        )
    if not settings.AVATAR_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Almacenamiento de avatares no configurado.",
        )

    object_name = f"avatars/{current_user.id}"
    data = await file.read()

    gcs = storage.Client()
    bucket = gcs.bucket(settings.AVATAR_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_string(data, content_type=file.content_type)

    base = str(request.base_url).rstrip("/")
    avatar_url = f"{base}/api/v1/users/{current_user.id}/avatar"
    current_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/{user_id}/avatar")
async def get_avatar(user_id: str) -> StreamingResponse:
    if not settings.AVATAR_BUCKET_NAME:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sin avatar.")

    object_name = f"avatars/{user_id}"
    try:
        gcs = storage.Client()
        bucket = gcs.bucket(settings.AVATAR_BUCKET_NAME)
        blob = bucket.blob(object_name)
        data = blob.download_as_bytes()
        content_type = blob.content_type or "image/jpeg"
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar no encontrado.")

    return StreamingResponse(iter([data]), media_type=content_type)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete (deactivate) the account. Data is retained. Use /me/data for full erasure."""
    current_user.is_active = False
    await db.commit()


@router.delete("/me/data", status_code=status.HTTP_204_NO_CONTENT)
async def erase_me(
    confirm: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """GDPR Art. 17 — permanent erasure of all personal data.

    Requires body: {"confirm": "DELETE MY ACCOUNT"}
    Deletes: Firestore plans, saved_events, and the user row.
    ON DELETE CASCADE handles child table rows automatically.
    """
    if confirm != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Envía {"confirm": "DELETE MY ACCOUNT"} para confirmar el borrado.',
        )

    # Delete Firestore plans belonging to this user
    firestore = get_firestore()
    plans_query = firestore.collection("plans").where(
        "user_id", "==", str(current_user.id)
    )
    plan_docs = await plans_query.get()
    for doc in plan_docs:
        await doc.reference.delete()

    # Hard-delete the user row; ON DELETE CASCADE removes saved_events
    await db.delete(current_user)
    await db.commit()


@router.get("/me/export")
async def export_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """GDPR Art. 15 / Art. 20 — data access and portability.

    Returns a JSON file containing all personal data held for the authenticated user.
    """
    import json

    saved_result = await db.execute(
        select(SavedEvent).where(SavedEvent.user_id == current_user.id)
    )

    saved_events = [
        SavedEventRead.model_validate(e).model_dump(mode="json")
        for e in saved_result.scalars().all()
    ]

    profile = UserRead.model_validate(current_user).model_dump(mode="json")

    export_data = {
        "profile": profile,
        "saved_events": saved_events,
        "plans_note": "Your AI planning conversations are available at GET /api/v1/plans",
    }

    content = json.dumps(export_data, indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="my-data.json"'},
    )
