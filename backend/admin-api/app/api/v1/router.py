from fastapi import APIRouter

from app.api.v1.endpoints import analytics, events, me, stats, users

router = APIRouter(prefix="/api/v1")
router.include_router(me.router)
router.include_router(stats.router)
router.include_router(users.router)
router.include_router(events.router)
router.include_router(analytics.router)
