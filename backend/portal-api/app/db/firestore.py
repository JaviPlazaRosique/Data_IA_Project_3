import os
import time

import firebase_admin
from firebase_admin import credentials, firestore_async

from app.config import settings


class _EmulatorCredential(credentials.Base):
    """Stub credential for local Firestore emulator — the emulator ignores auth."""

    def get_access_token(self) -> credentials.AccessTokenInfo:
        return credentials.AccessTokenInfo("local-emulator-token", time.time() + 3600)

    def get_credential(self):
        # The Firebase Admin SDK calls this to get a google-auth credentials object.
        # For the emulator, auth is never verified, so a dummy token is fine.
        from google.oauth2.credentials import Credentials as _GoogleCredentials
        return _GoogleCredentials(token="local-emulator-token")

    def serialize(self) -> dict:
        return {}


def get_firestore() -> firestore_async.AsyncClient:
    """Return the async Firestore client, initialising the Firebase app if needed."""
    if not firebase_admin._apps:
        if settings.FIREBASE_CREDENTIALS_JSON:
            cred: credentials.Base = credentials.Certificate(settings.FIREBASE_CREDENTIALS_JSON)
        elif os.environ.get("FIRESTORE_EMULATOR_HOST"):
            # Local emulator — no real GCP credentials required
            cred = _EmulatorCredential()
        else:
            cred = credentials.ApplicationDefault()

        options = {}
        if settings.GOOGLE_CLOUD_PROJECT:
            options["projectId"] = settings.GOOGLE_CLOUD_PROJECT

        firebase_admin.initialize_app(cred, options if options else None)

    return firestore_async.client()
