from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.firestore import get_firestore
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanRead, PlanUpdate

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    data = doc.to_dict()
    if data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    data = doc.to_dict()
    if data["user_id"] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if doc.to_dict()["user_id"] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan")
    await doc_ref.delete()
