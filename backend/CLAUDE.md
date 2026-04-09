# Backend context

## Read first (always)
- /docs/architecture.md — layer rules, folder structure, key decisions
- /docs/api_contracts.md — all endpoint specs (implement exactly as written)

## Current session
Укажи в начале: "Phase 2: Auth" или "fixing nutrition log bug"

## FastAPI patterns used in this project

### Dependency injection
```python
# В routers — всегда так, не импортируй db напрямую
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
```

### Service pattern
```python
# services/user_service.py
async def get_user_profile(db: AsyncSession, userId: int) -> UserOut:
    """Fetch user with computed BMI and TDEE."""
    ...
# Роутер вызывает сервис, не делает запросы сам
```

### Error handling
```python
raise HTTPException(status_code=404, detail="User not found")
# Никогда: return {"error": "not found"}
```

## Alembic rules
- Never edit DB manually — always create migration
- Migration naming: `alembic revision -m "add_restrictions_table"`
- Run after model change: `alembic upgrade head`

## Environment
All config via pydantic-settings from .env:
DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES