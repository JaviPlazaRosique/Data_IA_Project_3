import firebase_admin
from firebase_admin import credentials, firestore_async

from app.config import settings


def get_firestore() -> firestore_async.AsyncClient:
    """Return the async Firestore client, initialising the Firebase app if needed."""
    if not firebase_admin._apps:
        if settings.FIREBASE_CREDENTIALS_JSON:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_JSON)
        else:
            cred = credentials.ApplicationDefault()

        options = {}
        if settings.GOOGLE_CLOUD_PROJECT:
            options["projectId"] = settings.GOOGLE_CLOUD_PROJECT

        firebase_admin.initialize_app(cred, options if options else None)

    return firestore_async.client()
