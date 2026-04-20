from fastapi import APIRouter

from app.api.v1.endpoints import auth, events, plans, reviews, saved_events, users

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(plans.router)
router.include_router(saved_events.router)
router.include_router(events.router)
router.include_router(reviews.router)  # mounts /events/... and /users/me/reviews
