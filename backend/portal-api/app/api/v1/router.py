from fastapi import APIRouter

from app.api.v1.endpoints import events, plans, saved_events, swipe_events, users

router = APIRouter(prefix="/api/v1")
router.include_router(users.router)
router.include_router(plans.router)
router.include_router(saved_events.router)
router.include_router(swipe_events.router)
router.include_router(events.router)
