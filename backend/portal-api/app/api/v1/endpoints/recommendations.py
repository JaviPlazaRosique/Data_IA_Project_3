import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.recommendation import ClusterRecommendationRead
from app.services.recommendations import list_user_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/me/recommendations", tags=["recommendations"])


@router.get("", response_model=list[ClusterRecommendationRead])
async def list_recommendations(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> list[ClusterRecommendationRead]:
    try:
        return await list_user_recommendations(str(current_user.id), limit)
    except Exception:
        logger.exception("Failed to load cluster recommendations")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudieron cargar las recomendaciones",
        )
