import re
import unicodedata
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import credentials_exception, inactive_user_exception
from app.core.firebase_auth import verify_id_token
from app.db.session import AsyncSessionLocal
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def _username_from_email(email: str) -> str:
    base = email.split("@")[0][:90]
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in base) or "user"


def _slugify_username(name: str | None) -> str:
    if not name:
        return ""
    normalized = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in normalized if not unicodedata.combining(c))
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", stripped).strip("_").lower()
    slug = re.sub(r"_+", "_", slug)
    return slug[:90]


async def _resolve_unique_username(db: AsyncSession, base: str) -> str:
    candidate = base
    suffix = 1
    while True:
        existing = await db.execute(select(User).where(User.username == candidate))
        if not existing.scalar_one_or_none():
            return candidate
        suffix += 1
        candidate = f"{base}_{suffix}"


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise credentials_exception

    try:
        decoded = verify_id_token(creds.credentials)
    except Exception:
        raise credentials_exception

    uid: str | None = decoded.get("user_id") or decoded.get("uid") or decoded.get("sub")
    email: str | None = decoded.get("email")
    email_verified: bool = bool(decoded.get("email_verified"))
    name: str | None = decoded.get("name")
    picture: str | None = decoded.get("picture")
    sign_in_provider: str | None = (decoded.get("firebase") or {}).get("sign_in_provider")

    if not uid or not email:
        raise credentials_exception

    if sign_in_provider == "password" and not email_verified:
        raise credentials_exception

    result = await db.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalar_one_or_none()

    if user is None:
        existing_email = await db.execute(select(User).where(User.email == email))
        user = existing_email.scalar_one_or_none()
        if user is not None:
            user.firebase_uid = uid
            if user.full_name is None and name:
                user.full_name = name
            if user.avatar_url is None and picture:
                user.avatar_url = picture
        else:
            username_base = _slugify_username(name) or _username_from_email(email)
            username = await _resolve_unique_username(db, username_base)
            user = User(
                firebase_uid=uid,
                email=email,
                username=username,
                full_name=name,
                avatar_url=picture,
                is_verified=email_verified,
            )
            db.add(user)
        await db.commit()
        await db.refresh(user)

    if user.is_verified != email_verified:
        user.is_verified = email_verified
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise inactive_user_exception

    return user
