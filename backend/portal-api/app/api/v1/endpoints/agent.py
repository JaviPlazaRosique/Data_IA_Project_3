import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.limiter import limiter
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_engine import AgentEngineError, ask_agent
from app.services.model_armor import BlockReason, sanitize_user_prompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


_BLOCK_MESSAGES: dict[BlockReason, str] = {
    "injection": "No puedo procesar esa petición por motivos de seguridad.",
    "toxicity": "Tu mensaje contiene contenido no permitido.",
    "url": "Tu mensaje contiene enlaces no permitidos.",
    "sensitive_data": "Tu mensaje contiene datos sensibles que no puedo procesar.",
    "none": "",
}


@router.post("/chat", response_model=AgentChatResponse)
@limiter.limit("10/minute")
async def chat_with_agent(
    request: Request,
    body: AgentChatRequest,
    current_user: User = Depends(get_current_user),
) -> AgentChatResponse:
    session_id = body.session_id or f"planner-{uuid4()}"
    message = body.message.strip()

    sanitization = await sanitize_user_prompt(message)
    if sanitization.blocked:
        logger.info(
            "agent_chat_blocked",
            extra={
                "user_id": str(current_user.id),
                "reason": sanitization.reason,
                "confidence": sanitization.detail,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_BLOCK_MESSAGES[sanitization.reason],
        )

    try:
        answer = await ask_agent(
            user_id=str(current_user.id),
            session_id=session_id,
            message=message,
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
