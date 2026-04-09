from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user_schemas import AuthResponse, TokenResponse, UserCreate, UserOut, UserUpdate

ACTIVITY_FACTORS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def calculate_bmi(weightKg: float | None, heightCm: float | None) -> float | None:
    """Compute BMI rounded to one decimal; None if data is missing."""
    if weightKg is None or heightCm is None or heightCm == 0:
        return None
    heightM = heightCm / 100
    return round(weightKg / (heightM**2), 1)


def calculate_tdee(
    weightKg: float | None,
    heightCm: float | None,
    age: int | None,
    gender: str | None,
    activityLevel: str | None,
) -> int | None:
    """Compute TDEE via Mifflin-St Jeor; None if any required value is missing."""
    if any(v is None for v in [weightKg, heightCm, age, gender, activityLevel]):
        return None
    if gender == "male":
        bmr = (10 * weightKg) + (6.25 * heightCm) - (5 * age) + 5
    elif gender == "female":
        bmr = (10 * weightKg) + (6.25 * heightCm) - (5 * age) - 161
    else:
        male_bmr = (10 * weightKg) + (6.25 * heightCm) - (5 * age) + 5
        female_bmr = (10 * weightKg) + (6.25 * heightCm) - (5 * age) - 161
        bmr = (male_bmr + female_bmr) / 2
    return round(bmr * ACTIVITY_FACTORS.get(activityLevel, 1.2))


def _to_user_out(user: User) -> UserOut:
    """Build UserOut from ORM instance, injecting computed BMI and TDEE."""
    base = UserOut.model_validate(user)
    return base.model_copy(
        update={
            "bmi": calculate_bmi(user.weightKg, user.heightCm),
            "tdee": calculate_tdee(
                user.weightKg, user.heightCm, user.age, user.gender, user.activityLevel
            ),
        }
    )


async def register_user(db: AsyncSession, data: UserCreate) -> AuthResponse:
    """Register a new user; raise 409 if email already exists."""
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise AppError(status.HTTP_409_CONFLICT, "Email already registered", "EMAIL_EXISTS")
    user = User(
        email=data.email,
        passwordHash=hash_password(data.password),
        age=data.age,
        weightKg=data.weightKg,
        heightCm=data.heightCm,
        gender=data.gender,
        activityLevel=data.activityLevel,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(user=_to_user_out(user), accessToken=create_access_token(user.id))


async def authenticate_user(db: AsyncSession, email: str, password: str) -> TokenResponse:
    """Validate credentials and return a token; raise 401 on failure."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.passwordHash):
        raise AppError(status.HTTP_401_UNAUTHORIZED, "Invalid credentials", "AUTH_FAILED")
    return TokenResponse(accessToken=create_access_token(user.id))


async def get_user_profile(db: AsyncSession, userId: int) -> UserOut:
    """Return user profile with computed BMI and TDEE."""
    user = await db.get(User, userId)
    if user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    return _to_user_out(user)


async def update_user_profile(db: AsyncSession, userId: int, data: UserUpdate) -> UserOut:
    """Apply partial update to user profile and return updated result."""
    user = await db.get(User, userId)
    if user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    for field, value in data.model_dump(exclude_none=True, by_alias=False).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return _to_user_out(user)
