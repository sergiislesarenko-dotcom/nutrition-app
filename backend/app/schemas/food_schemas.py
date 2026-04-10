from pydantic import BaseModel, ConfigDict, Field


class FoodOut(BaseModel):
    """Schema for a food record with per-100g nutritional values."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    caloriesPer100g: float = Field(serialization_alias="calories_per_100g")
    proteinPer100g: float = Field(serialization_alias="protein_per_100g")
    carbsPer100g: float = Field(serialization_alias="carbs_per_100g")
    fatPer100g: float = Field(serialization_alias="fat_per_100g")


class FoodMacrosOut(BaseModel):
    """Schema for calculated macros at a specific weight."""

    food: FoodOut
    weightG: float = Field(serialization_alias="weight_g")
    caloriesKcal: float = Field(serialization_alias="calories_kcal")
    proteinG: float = Field(serialization_alias="protein_g")
    carbsG: float = Field(serialization_alias="carbs_g")
    fatG: float = Field(serialization_alias="fat_g")


class FoodSearchResponse(BaseModel):
    """Schema for food autocomplete search results."""

    results: list[FoodOut]


class KnownMacros(BaseModel):
    """Partial per-100g macro values provided by the user (all optional)."""

    calories_per_100g: float | None = None
    protein_per_100g: float | None = None
    carbs_per_100g: float | None = None
    fat_per_100g: float | None = None


class FoodCompleteRequest(BaseModel):
    """Request to fill in missing macro values for a food."""

    name: str = Field(min_length=1, max_length=255)
    weight_g: float = Field(gt=0)
    known: KnownMacros
