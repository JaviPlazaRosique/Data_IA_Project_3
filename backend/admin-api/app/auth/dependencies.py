from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase_auth import verify_id_token
from app.db.session import AsyncSessionLocal
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or missing credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Admin access required",
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_admin_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise _credentials_exception

    try:
        decoded = verify_id_token(creds.credentials)
    except Exception:
        raise _credentials_exception

    uid: str | None = decoded.get("user_id") or decoded.get("uid") or decoded.get("sub")
    email: str | None = decoded.get("email")

    if not uid or not email:
        raise _credentials_exception

    result = await db.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalar_one_or_none()

    if user is None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise _forbidden_exception

    if not user.is_admin:
        raise _forbidden_exception

    return user
