import json
import logging
from concurrent.futures import Future
from typing import Any

from google.cloud import pubsub_v1

from app.config import settings

logger = logging.getLogger(__name__)

_publisher: pubsub_v1.PublisherClient | None = None


def _get_publisher() -> pubsub_v1.PublisherClient:
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


def _topic_path(topic: str) -> str:
    if not settings.GOOGLE_CLOUD_PROJECT:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT must be set to publish to Pub/Sub")
    return _get_publisher().topic_path(settings.GOOGLE_CLOUD_PROJECT, topic)


def _log_publish_result(topic_path: str) -> "callable":
    def _cb(future: Future) -> None:
        try:
            message_id = future.result(timeout=0)
            logger.info("published swipe to %s id=%s", topic_path, message_id)
        except Exception:
            logger.exception("failed to publish swipe to %s", topic_path)

    return _cb


def publish_swipe_event(payload: dict[str, Any]) -> None:
    """Fire-and-forget publish. Errors are logged from the future callback."""
    publisher = _get_publisher()
    topic_path = _topic_path(settings.PUBSUB_TOPIC_SWIPE_EVENTS)
    data = json.dumps(payload, default=str).encode("utf-8")
    attributes = {"event_type": "swipe"}
    if "user_id" in payload:
        attributes["user_id"] = str(payload["user_id"])
    if "direction" in payload:
        attributes["direction"] = str(payload["direction"])

    future = publisher.publish(topic_path, data, **attributes)
    future.add_done_callback(_log_publish_result(topic_path))
