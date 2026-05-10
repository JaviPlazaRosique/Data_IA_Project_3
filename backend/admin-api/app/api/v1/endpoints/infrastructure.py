import asyncio
import time
from urllib.request import urlopen
from urllib.error import URLError

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_admin_user, get_db
from app.config import settings
from app.db.bigquery import get_bq_client
from app.db.firestore import get_firestore
from app.models.user import User

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])

ServiceStatus = str  # "ok" | "degraded" | "error" | "unknown"


class ServiceCheck(BaseModel):
    name: str
    status: ServiceStatus
    latency_ms: int | None = None
    detail: str | None = None


class InfrastructureResponse(BaseModel):
    services: list[ServiceCheck]


def _http_check(url: str, timeout: int = 5) -> ServiceCheck:
    name = url.split("//")[-1].split(".")[0]
    start = time.monotonic()
    try:
        with urlopen(url, timeout=timeout) as resp:
            latency_ms = round((time.monotonic() - start) * 1000)
            if resp.status < 400:
                return ServiceCheck(name=name, status="ok", latency_ms=latency_ms)
            return ServiceCheck(name=name, status="degraded", latency_ms=latency_ms, detail=f"HTTP {resp.status}")
    except URLError as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name=name, status="error", latency_ms=latency_ms, detail=str(e.reason))
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name=name, status="error", latency_ms=latency_ms, detail=str(e))


def _bq_check() -> ServiceCheck:
    start = time.monotonic()
    try:
        list(get_bq_client().query("SELECT 1").result())
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name="bigquery", status="ok", latency_ms=latency_ms)
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name="bigquery", status="error", latency_ms=latency_ms, detail=str(e)[:120])


async def _db_check(db: AsyncSession) -> ServiceCheck:
    start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name="cloudsql", status="ok", latency_ms=latency_ms)
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name="cloudsql", status="error", latency_ms=latency_ms, detail=str(e)[:120])


async def _firestore_check() -> ServiceCheck:
    start = time.monotonic()
    try:
        fs = get_firestore()
        await fs.collection("eventos").limit(1).get()
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name="firestore", status="ok", latency_ms=latency_ms)
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return ServiceCheck(name="firestore", status="error", latency_ms=latency_ms, detail=str(e)[:120])


@router.get("", response_model=InfrastructureResponse)
async def get_infrastructure(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> InfrastructureResponse:
    checks: list[ServiceCheck] = []

    admin_check = ServiceCheck(name="admin-api", status="ok", latency_ms=0)
    checks.append(admin_check)

    db_check, fs_check, bq_check = await asyncio.gather(
        _db_check(db),
        _firestore_check(),
        asyncio.to_thread(_bq_check),
    )
    checks.append(db_check)
    checks.append(fs_check)
    checks.append(bq_check)

    portal_url = settings.PORTAL_API_URL
    if portal_url:
        portal_check = await asyncio.to_thread(_http_check, f"{portal_url}/api/health")
        portal_check.name = "portal-api"
        checks.append(portal_check)

    return InfrastructureResponse(services=checks)
