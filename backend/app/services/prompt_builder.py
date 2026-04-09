from datetime import date

from app.models.goal import Goal
from app.models.restriction import Restriction
from app.models.user import User
from app.schemas.nutrition_schemas import NutritionLogOut


def _profile_section(user: User, bmi: float | None, tdee: int | None) -> str:
    """Render the user profile block."""
    lines = [
        f"Age: {user.age}, Gender: {user.gender}",
        f"Weight: {user.weightKg} kg, Height: {user.heightCm} cm",
        f"BMI: {bmi if bmi is not None else 'n/a'}",
        f"TDEE: {tdee if tdee is not None else 'n/a'} kcal/day",
    ]
    return "User profile:\n" + "\n".join(f"  {l}" for l in lines)


def _goal_section(goal: Goal | None) -> str:
    """Render the active goal block."""
    if goal is None:
        return "Current goal: none set"
    parts = [f"type={goal.goalType}"]
    if goal.targetWeightKg:
        parts.append(f"target={goal.targetWeightKg} kg")
    if goal.dailyCaloriesKcal:
        parts.append(f"daily_calories={goal.dailyCaloriesKcal} kcal")
    if goal.deadline:
        parts.append(f"deadline={goal.deadline}")
    return "Current goal: " + ", ".join(parts)


def _restrictions_section(restrictions: list[Restriction]) -> str:
    """Render dietary/medical restrictions."""
    if not restrictions:
        return "Restrictions: none"
    items = "\n".join(f"  [{r.type}] {r.value}" for r in restrictions)
    return f"Restrictions:\n{items}"


def _logs_section(logs: list[NutritionLogOut], goal: Goal | None) -> str:
    """Render today's food log with totals."""
    today = date.today().isoformat()
    if not logs:
        return f"Today's intake ({today}): no entries yet"
    lines = [f"Today's intake ({today}):"]
    total_kcal = total_p = total_c = total_f = 0.0
    for log in logs:
        lines.append(
            f"  [{log.mealType}] {log.foodName} — "
            f"{log.caloriesKcal} kcal, P:{log.proteinG}g C:{log.carbsG}g F:{log.fatG}g"
        )
        total_kcal += log.caloriesKcal
        total_p += log.proteinG
        total_c += log.carbsG
        total_f += log.fatG
    lines.append(
        f"  Total: {total_kcal:.0f} kcal | P:{total_p:.0f}g C:{total_c:.0f}g F:{total_f:.0f}g"
    )
    if goal and goal.dailyCaloriesKcal:
        diff = total_kcal - goal.dailyCaloriesKcal
        label = "surplus" if diff >= 0 else "deficit"
        lines.append(f"  vs goal: {abs(diff):.0f} kcal {label}")
    return "\n".join(lines)


def build_system_prompt(
    user: User,
    goal: Goal | None,
    restrictions: list[Restriction],
    logs: list[NutritionLogOut],
    bmi: float | None,
    tdee: int | None,
) -> str:
    """Assemble the full system prompt with user context for the AI assistant."""
    sections = [
        "You are a personal AI nutrition assistant. "
        "Answer concisely based on the user's actual data below. "
        "Give specific, actionable advice. Do not repeat the data back verbatim.",
        _profile_section(user, bmi, tdee),
        _goal_section(goal),
        _restrictions_section(restrictions),
        _logs_section(logs, goal),
    ]
    return "\n\n".join(sections)
