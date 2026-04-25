import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from app.core.limiter import limiter
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.saved_event import SwipeEventAccepted, SwipeEventCreate
from app.services.pubsub import publish_swipe_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/me/swipe-events", tags=["swipe-events"])


@router.post(
    "",
    response_model=SwipeEventAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("10/second")
async def publish_swipe(
    request: Request,
    body: SwipeEventCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> SwipeEventAccepted:
    payload = body.model_dump()
    payload["user_id"] = str(current_user.id)
    if body.swiped_at is None:
        payload["swiped_at"] = datetime.now(timezone.utc)

    background_tasks.add_task(publish_swipe_event, payload)
    return SwipeEventAccepted(accepted=True)
