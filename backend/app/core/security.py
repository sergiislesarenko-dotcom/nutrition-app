from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE = "bearer"


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return PWD_CONTEXT.hash(password)


def verify_password(plainPassword: str, hashedPassword: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return PWD_CONTEXT.verify(plainPassword, hashedPassword)


def create_access_token(subject: Any) -> str:
    """Create a signed JWT access token with expiry."""
    expireMinutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expireMinutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> str | None:
    """Decode and validate a JWT; return subject string or None."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("sub")
    except JWTError:
        return None
