from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import verify_token

BEARER_SCHEME = HTTPBearer()


async def get_db() -> AsyncSession:
    """Yield an async database session, closing it after the request."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(BEARER_SCHEME),
) -> int:
    """Extract and validate user ID from Bearer token."""
    token = credentials.credentials
    subject = verify_token(token)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return int(subject)
