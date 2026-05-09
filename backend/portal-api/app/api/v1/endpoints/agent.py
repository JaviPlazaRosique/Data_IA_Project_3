import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_engine import AgentEngineError, ask_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    body: AgentChatRequest,
    current_user: User = Depends(get_current_user),
) -> AgentChatResponse:
    session_id = body.session_id or f"planner-{uuid4()}"
    try:
        answer = await ask_agent(
            user_id=str(current_user.id),
            session_id=session_id,
            message=body.message.strip(),
        )
    except AgentEngineError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("agent_chat_failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo obtener respuesta del agente",
        ) from exc

    return AgentChatResponse(answer=answer, session_id=session_id)
