from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration request body."""

    email: EmailStr
    password: str = Field(min_length=8)
    age: int = Field(ge=1, le=150)
    weightKg: float = Field(alias="weight_kg", gt=0)
    heightCm: float = Field(alias="height_cm", gt=0)
    gender: str = Field(pattern="^(male|female|other)$")
    activityLevel: str = Field(
        alias="activity_level",
        pattern="^(sedentary|light|moderate|active|very_active)$",
    )

    model_config = ConfigDict(populate_by_name=True)


class UserOut(BaseModel):
    """Schema for user profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    age: int | None
    weightKg: float | None = Field(serialization_alias="weight_kg")
    heightCm: float | None = Field(serialization_alias="height_cm")
    gender: str | None
    activityLevel: str | None = Field(serialization_alias="activity_level")
    bmi: float | None = None
    tdee: int | None = None
    createdAt: datetime = Field(serialization_alias="created_at")


class LoginRequest(BaseModel):
    """Schema for login request body."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for login response."""

    accessToken: str = Field(serialization_alias="access_token")
    tokenType: str = Field(default="bearer", serialization_alias="token_type")


class AuthResponse(BaseModel):
    """Schema for registration response."""

    user: UserOut
    accessToken: str = Field(serialization_alias="access_token")
    tokenType: str = Field(default="bearer", serialization_alias="token_type")


class UserUpdate(BaseModel):
    """Schema for partial user profile update."""

    age: int | None = Field(default=None, ge=1, le=150)
    weightKg: float | None = Field(default=None, alias="weight_kg", gt=0)
    heightCm: float | None = Field(default=None, alias="height_cm", gt=0)
    gender: str | None = Field(default=None, pattern="^(male|female|other)$")
    activityLevel: str | None = Field(
        default=None,
        alias="activity_level",
        pattern="^(sedentary|light|moderate|active|very_active)$",
    )

    model_config = ConfigDict(populate_by_name=True)
