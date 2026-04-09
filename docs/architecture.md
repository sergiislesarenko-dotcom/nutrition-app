# Architecture decisions

## Layer structure (backend)
Request → Router → Service → Repository → DB
- Routers: HTTP only, validation via Pydantic, no business logic
- Services: all business logic, call repositories
- Repositories: all DB queries via SQLAlchemy, no logic
- Never skip layers (router → DB directly is forbidden)

## Database schema (summary)
users:          id, email, password_hash, age, weight_kg, height_cm,
                gender, activity_level, created_at
goals:          id, user_id(FK), goal_type, target_weight_kg,
                daily_calories_kcal, deadline, is_active
nutrition_logs: id, user_id(FK), logged_at, meal_type,
                food_name, weight_g, calories_kcal,
                protein_g, carbs_g, fat_g
restrictions:   id, user_id(FK), type(dietary|medical|allergy), value
recommendations: id, user_id(FK), question, answer, created_at

## Key decisions & why
- MySQL 8 not PostgreSQL: team familiarity, JSON column support enough
- SQLAlchemy async (not sync): FastAPI is async-first, consistency
- Alembic for migrations: never edit DB schema manually
- JWT stateless (no refresh token in DB): simplicity for MVP
  → revisit if session revocation needed in v2
- Claude API called per-request (no caching): responses must be
  personalised to latest nutrition log data
- SSE not WebSocket for AI streaming: simpler, HTTP-compatible,
  no persistent connection management needed

## Folder structure
backend/
  app/
    core/       config.py, database.py, security.py, dependencies.py
    models/     user.py, goal.py, nutrition_log.py, recommendation.py
    schemas/    user_schemas.py, nutrition_schemas.py, ai_schemas.py
    services/   user_service.py, nutrition_service.py, ai_service.py
    routers/    auth_router.py, user_router.py, nutrition_router.py,
                ai_router.py
  tests/
    conftest.py
    test_auth.py, test_nutrition.py, test_ai.py

## What belongs where (quick ref)
- КБЖУ calculation logic → nutrition_service.py
- Prompt building → ai_service.py (only here, nowhere else)
- JWT creation/validation → core/security.py
- DB session management → core/dependencies.py via Depends()