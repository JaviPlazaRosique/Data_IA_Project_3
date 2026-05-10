from fastapi import APIRouter

from app.api.v1.endpoints import analytics, events, infrastructure, kpis, me, saved_events, stats, users

router = APIRouter(prefix="/api/v1")
router.include_router(me.router)
router.include_router(stats.router)
router.include_router(users.router)
router.include_router(events.router)
router.include_router(analytics.router)
router.include_router(saved_events.router)
router.include_router(infrastructure.router)
router.include_router(kpis.router)
