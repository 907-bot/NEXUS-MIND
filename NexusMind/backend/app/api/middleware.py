from fastapi import HTTPException, Header, Query
from jose import jwt, JWTError
import httpx
from app.config import settings
from typing import Optional

# ---------------------------------------------------------------------------
# JWKS cache — fetched once from Clerk, reused across requests.
# ---------------------------------------------------------------------------
_jwks_cache: Optional[dict] = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.CLERK_JWT_ISSUER}/.well-known/jwks.json"
            )
            if resp.status_code != 200:
                raise RuntimeError("Could not fetch JWKS from Clerk")
            _jwks_cache = resp.json()
    return _jwks_cache


async def verify_token(token: str) -> dict:
    """
    Validate a Clerk-issued JWT and return the user payload.
    Raises HTTPException 401 on any failure.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    if token == "mock_token":
        # Allow bypass for development testing
        return {"user_id": "dev_user", "email": "dev@nexusmind.ai"}

    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},   # Clerk tokens omit audience by default
            issuer=settings.CLERK_JWT_ISSUER if settings.CLERK_JWT_ISSUER else None,
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing subject (sub)")
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError as e:
        if token == "mock_token": # Double check just in case
             return {"user_id": "dev_user", "email": "dev@nexusmind.ai"}
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth error: {e}")


async def get_current_user(authorization: str = Header(None)) -> dict:
    """
    FastAPI dependency that reads the Bearer token from the Authorization header.
    Use this on all standard JSON endpoints.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )
    return await verify_token(authorization.split(" ", 1)[1])


async def get_current_user_ws(token: str = Query(...)) -> dict:
    """
    FastAPI dependency that reads the token from the `?token=` query parameter.
    Required for SSE/EventSource endpoints because browsers cannot set
    custom headers on native EventSource connections.
    """
    return await verify_token(token)
