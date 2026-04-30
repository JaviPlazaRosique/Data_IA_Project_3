import json
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

from app.config import settings

logger = logging.getLogger(__name__)

ZONA_MADRID = ZoneInfo("Europe/Madrid")

_cliente: tasks_v2.CloudTasksClient | None = None


def _get_cliente() -> tasks_v2.CloudTasksClient:
    global _cliente
    if _cliente is None:
        _cliente = tasks_v2.CloudTasksClient()
    return _cliente


def programar_email_valoracion(id_usuario: str, id_evento: str, nombre_evento: str, fecha_evento: str) -> None:
    try:
        fecha_base = datetime.strptime(fecha_evento, "%Y-%m-%d")
        envio = datetime(
            fecha_base.year, fecha_base.month, fecha_base.day,
            12, 0, 0,
            tzinfo=ZONA_MADRID,
        ) + timedelta(days=1)

        if envio <= datetime.now(timezone.utc):
            logger.info("Fecha de envío ya pasada para evento %s, no se crea task", id_evento)
            return

        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(envio.astimezone(timezone.utc))

        cuerpo = json.dumps({
            "user_id":    id_usuario,
            "event_id":   id_evento,
            "event_name": nombre_evento,
        }).encode()

        tarea = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url":         settings.RATING_EMAIL_FUNCTION_URL,
                "headers":     {"Content-Type": "application/json"},
                "body":        cuerpo,
                "oidc_token": {
                    "service_account_email": settings.RATING_FUNCTION_SA_EMAIL,
                    "audience":              settings.RATING_EMAIL_FUNCTION_URL,
                },
            },
            "schedule_time": ts,
        }

        _get_cliente().create_task(parent=settings.CLOUD_TASKS_QUEUE_PATH, task=tarea)
        logger.info(
            "Task de valoración creada: usuario=%s evento=%s envio=%s",
            id_usuario, id_evento, envio.isoformat(),
        )

    except Exception:
        logger.exception("Error creando task de valoración para evento %s", id_evento)
