# AI Nutrition App — Project Context

## Project overview
AI-powered nutrition tracking app. Users log meals, get personalized
recommendations via Claude API based on their profile, goals, and restrictions.

## Tech stack
- Backend: FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic, MySQL 8
- Frontend: React 18, TypeScript, TanStack Query, Axios
- Mobile: React Native (cross-platform), Swift (iOS), Kotlin (Android)
- AI: Anthropic Claude API (claude-sonnet-4-20250514)
- Infra: Docker Compose, pytest, Vitest

## Naming conventions — ALWAYS follow these

### Python (backend)
- Variables and class attributes: camelCase → userName, targetWeight
- Functions and methods: snake_case → get_user_profile(), build_system_prompt()
- Classes: PascalCase → UserProfile, NutritionLog
- Constants: UPPER_SNAKE → MAX_HISTORY_DAYS, DEFAULT_CALORIES
- Files/modules: snake_case → user_service.py, nutrition_router.py
- Database columns: snake_case → user_id, created_at, target_weight

### TypeScript/JavaScript (frontend + mobile)
- Variables and functions: camelCase → userName, getUserProfile()
- React components: PascalCase → UserProfileCard, NutritionChart
- Types/Interfaces: PascalCase, prefix I for interfaces → IUserProfile
- Constants: UPPER_SNAKE → API_BASE_URL, MAX_RETRY_COUNT
- Files: kebab-case → user-profile.tsx, nutrition-chart.tsx
- CSS classes: kebab-case → user-card, nutrition-log-item

## Architecture rules
- Each router file handles ONE resource only (users, nutrition, ai)
- Business logic lives in services/, never in routers/
- Pydantic schemas in schemas/ are separate from SQLAlchemy models/
- No direct DB calls from routers — always go through a service
- All AI prompt logic lives ONLY in services/ai/prompt_builder.py

## Development phases — current status
- [x] Phase 1: Infrastructure (docker, DB, migrations)
- [ ] Phase 2: Auth service (JWT, user profile CRUD)
- [ ] Phase 3: Nutrition core (food logs, КБЖУ, goals)
- [ ] Phase 4: AI service (Claude API, streaming)
- [ ] Phase 5: Frontend (React, React Native)

## Testing requirements
- Every new service function MUST have a pytest test
- Use fixtures in conftest.py — never create test data inline
- Mock Claude API calls in tests with pytest-mock
- Run tests before marking a phase complete: `pytest tests/ -v`

## Context window rules — IMPORTANT
- When working on backend/auth: do NOT read frontend files
- When working on a single service: read only its router + service + schema
- Always specify which phase you're working on at the start of a session
- If a file is >200 lines, ask Claude to read only the relevant section

## Code style
- Max function length: 30 lines. If longer — split into helpers
- Max file length: 200 lines. If longer — split the module
- Every function needs a docstring (one line is enough)
- No magic numbers — use named constants
- Prefer explicit over implicit (type hints everywhere in Python)

## Git & GitHub workflow

### Branch strategy
- main — только стабильный код, прямые пушы запрещены
- develop — основная ветка разработки
- feature/phase-1-infrastructure — ветка для каждого этапа
- feature/auth-jwt — ветка для отдельной фичи внутри этапа
- fix/nutrition-calories-calc — ветка для багфиксов

### Before starting any work
Always check current branch and status:
  git status
  git pull origin develop

### Commit message format (Conventional Commits)
<type>(<scope>): <short description in Russian or English>

Types:
  feat     — новая функциональность
  fix      — исправление бага
  refactor — рефакторинг без изменения поведения
  test     — добавление/изменение тестов
  docs     — изменения в документации
  chore    — настройка окружения, зависимости

Examples:
  feat(auth): add JWT refresh token endpoint
  fix(nutrition): fix calorie calculation for composite meals
  test(ai): add mock tests for Claude API streaming
  refactor(user): split user_service into profile and goals modules

### Commit rules
- Commit after each logical unit of work (не весь этап одним коммитом)
- Never commit: .env, __pycache__, node_modules, *.pyc
- Always run tests before committing: pytest tests/ -v
- One concern per commit — не мешай feat и refactor в один коммит

### Pull Request rules
- PR title = последний коммит или краткое описание этапа
- PR из feature/* → develop (не в main напрямую)
- Squash commits при мерже если больше 5 коммитов в ветке

### .gitignore must include
.env
.env.*
__pycache__/
*.pyc
.pytest_cache/
node_modules/
.DS_Store

## Project map — key files

docs/
  architecture.md     — DB schema, layer rules, key decisions
  api_contracts.md    — all endpoints, request/response shapes

backend/
  CLAUDE.md           — backend-specific context
  app/core/config.py  — env vars, settings
  app/core/database.py — SQLAlchemy engine and session
  alembic/versions/   — DB migrations (never edit manually)

frontend/
  CLAUDE.md           — frontend-specific context
  src/services/api.ts — axios instance (single source)
  src/types/api.types.ts — mirrors api_contracts.md schemas

mobile/
  CLAUDE.md           — mobile-specific context

## When in doubt where a file lives — check this map first.
## Never assume a path — ask if unsure.