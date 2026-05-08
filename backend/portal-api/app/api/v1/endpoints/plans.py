import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from slowapi.util import get_remote_address

from app.core.limiter import limiter
from app.db.firestore import get_firestore
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.plan import ChatRequest, ChatResponse, PlanCreate, PlanMessage, PlanRead, PlanUpdate
from app.services.chatbot import generate_chat_reply
from app.services.recommendations import list_user_recommendations
from app.services.user_profile import UserTasteProfile, fetch_user_taste_profile


def _user_id_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.get_unverified_claims(auth[7:])
            uid = payload.get("user_id") or payload.get("uid") or payload.get("sub")
            if uid:
                return f"user:{uid}"
        except JWTError:
            pass
    return get_remote_address(request)

router = APIRouter(prefix="/plans", tags=["plans"])

COLLECTION = "plans"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _expiry_iso() -> str:
    """12-month TTL from now. Firestore TTL policy on expires_at handles auto-deletion."""
    return (datetime.now(UTC) + timedelta(days=365)).isoformat()


def _doc_to_plan(plan_id: str, data: dict) -> PlanRead:
    return PlanRead(
        plan_id=plan_id,
        user_id=data["user_id"],
        title=data.get("title", ""),
        messages=data.get("messages", []),
        itinerary=data.get("itinerary", {}),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


@router.get("", response_model=list[PlanRead])
async def list_plans(
    current_user: User = Depends(get_current_user),
) -> list[PlanRead]:
    db = get_firestore()
    query = (
        db.collection(COLLECTION)
        .where("user_id", "==", str(current_user.id))
        .order_by("updated_at", direction="DESCENDING")
    )
    docs = await query.get()
    return [_doc_to_plan(doc.id, doc.to_dict()) for doc in docs]


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    body: PlanCreate,
    current_user: User = Depends(get_current_user),
) -> PlanRead:
    db = get_firestore()
    now = _now_iso()
    payload = {
        "user_id": str(current_user.id),
        "title": body.title,
        "messages": [m.model_dump() for m in body.messages],
        "itinerary": body.itinerary.model_dump(),
        "created_at": now,
        "updated_at": now,
        "expires_at": _expiry_iso(),  # GDPR Art. 5(1)(e) — 12-month retention TTL
    }
    _write_result, doc_ref = await db.collection(COLLECTION).add(payload)
    return _doc_to_plan(doc_ref.id, payload)


@router.get("/{plan_id}", response_model=PlanRead)
async def get_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
) -> PlanRead:
    db = get_firestore()
    doc = await db.collection(COLLECTION).document(plan_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    data = doc.to_dict()
    if data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este plan no te pertenece")
    return _doc_to_plan(plan_id, data)


@router.put("/{plan_id}", response_model=PlanRead)
async def update_plan(
    plan_id: str,
    body: PlanUpdate,
    current_user: User = Depends(get_current_user),
) -> PlanRead:
    db = get_firestore()
    doc_ref = db.collection(COLLECTION).document(plan_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    data = doc.to_dict()
    if data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este plan no te pertenece")

    updates: dict = {"updated_at": _now_iso(), "expires_at": _expiry_iso()}
    if body.title is not None:
        updates["title"] = body.title
    if body.messages is not None:
        updates["messages"] = [m.model_dump() for m in body.messages]
    if body.itinerary is not None:
        updates["itinerary"] = body.itinerary.model_dump()

    await doc_ref.update(updates)
    data.update(updates)
    return _doc_to_plan(plan_id, data)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    db = get_firestore()
    doc_ref = db.collection(COLLECTION).document(plan_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    if doc.to_dict()["user_id"] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este plan no te pertenece")
    await doc_ref.delete()


@router.post("/{plan_id}/chat", response_model=ChatResponse)
@limiter.limit("20/minute", key_func=_user_id_key)
async def chat_with_plan(
    request: Request,
    plan_id: str,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    db = get_firestore()
    doc_ref = db.collection(COLLECTION).document(plan_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    data = doc.to_dict()
    if data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este plan no te pertenece")

    user_msg = PlanMessage(role="user", content=body.content, timestamp=_now_iso())
    existing = [PlanMessage(**m) for m in data.get("messages", [])]
    all_messages = existing + [user_msg]

    rec_result, profile_result = await asyncio.gather(
        list_user_recommendations(str(current_user.id), limit=10),
        fetch_user_taste_profile(str(current_user.id)),
        return_exceptions=True,
    )
    recommendations = rec_result if not isinstance(rec_result, BaseException) else []
    user_profile: UserTasteProfile | None = profile_result if not isinstance(profile_result, BaseException) else None

    try:
        reply_text = await generate_chat_reply(all_messages, recommendations, user_profile)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El asistente no está disponible ahora mismo",
        ) from exc

    reply_ts = _now_iso()
    assistant_msg = PlanMessage(role="assistant", content=reply_text, timestamp=reply_ts)
    updated_messages = all_messages + [assistant_msg]

    await doc_ref.update({
        "messages": [m.model_dump() for m in updated_messages],
        "updated_at": reply_ts,
        "expires_at": _expiry_iso(),
    })

    return ChatResponse(content=reply_text, timestamp=reply_ts)
