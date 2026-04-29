from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings

_request = google_requests.Request()


def verify_id_token(token: str) -> dict:
    project_id = settings.FIREBASE_AUTH_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("FIREBASE_AUTH_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set")
    return id_token.verify_firebase_token(token, _request, audience=project_id)
