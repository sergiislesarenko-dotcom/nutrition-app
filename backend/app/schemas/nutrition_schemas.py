from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class NutritionLogCreate(BaseModel):
    """Schema for creating a nutrition log entry."""

    mealType: str = Field(
        alias="meal_type", pattern="^(breakfast|lunch|dinner|snack)$"
    )
    foodName: str = Field(alias="food_name", min_length=1, max_length=255)
    weightG: float = Field(alias="weight_g", gt=0)
    caloriesKcal: float = Field(alias="calories_kcal", ge=0)
    proteinG: float = Field(alias="protein_g", ge=0)
    carbsG: float = Field(alias="carbs_g", ge=0)
    fatG: float = Field(alias="fat_g", ge=0)
    loggedAt: datetime | None = Field(default=None, alias="logged_at")

    model_config = ConfigDict(populate_by_name=True)


class NutritionLogOut(BaseModel):
    """Schema for nutrition log entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    userId: int = Field(serialization_alias="user_id")
    mealType: str = Field(serialization_alias="meal_type")
    foodName: str = Field(serialization_alias="food_name")
    weightG: float = Field(serialization_alias="weight_g")
    caloriesKcal: float = Field(serialization_alias="calories_kcal")
    proteinG: float = Field(serialization_alias="protein_g")
    carbsG: float = Field(serialization_alias="carbs_g")
    fatG: float = Field(serialization_alias="fat_g")
    loggedAt: datetime = Field(serialization_alias="logged_at")


class GoalCreate(BaseModel):
    """Schema for creating a user goal."""

    goalType: str = Field(
        alias="goal_type",
        pattern="^(weight_loss|muscle_gain|maintenance|health)$",
    )
    targetWeightKg: float | None = Field(
        default=None, alias="target_weight_kg", gt=0
    )
    dailyCaloriesKcal: int | None = Field(
        default=None, alias="daily_calories_kcal", gt=0
    )
    deadline: date | None = None

    model_config = ConfigDict(populate_by_name=True)


class GoalOut(BaseModel):
    """Schema for goal response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    goalType: str = Field(serialization_alias="goal_type")
    targetWeightKg: float | None = Field(serialization_alias="target_weight_kg")
    dailyCaloriesKcal: int | None = Field(serialization_alias="daily_calories_kcal")
    deadline: date | None
    isActive: bool = Field(serialization_alias="is_active")


class RestrictionCreate(BaseModel):
    """Schema for creating a dietary/medical restriction."""

    type: str = Field(pattern="^(dietary|medical|allergy)$")
    value: str = Field(min_length=1, max_length=255)


class RestrictionOut(BaseModel):
    """Schema for restriction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    value: str


class DaySummary(BaseModel):
    """Schema for daily nutrition summary."""

    totalCalories: float = Field(serialization_alias="total_calories")
    totalProtein: float = Field(serialization_alias="total_protein")
    totalCarbs: float = Field(serialization_alias="total_carbs")
    totalFat: float = Field(serialization_alias="total_fat")
    goalCalories: int | None = Field(serialization_alias="goal_calories")
    deficitSurplus: float | None = Field(serialization_alias="deficit_surplus")


class NutritionLogsResponse(BaseModel):
    """Schema for paginated nutrition logs with daily summary."""

    logs: list[NutritionLogOut]
    summary: DaySummary
