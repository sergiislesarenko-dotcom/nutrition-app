# API contracts

## Changelog

## Base URL
Development: http://localhost:8000/api/v1
Production:  https://api.nutrition-app.com/api/v1

## Auth headers
All protected endpoints require:
  Authorization: Bearer <access_token>

## Endpoints

### Auth

POST /auth/register
Request:
  { "email": str, "password": str, "age": int,
    "weight_kg": float, "height_cm": float,
    "gender": "male"|"female"|"other",
    "activity_level": "sedentary"|"light"|"moderate"|"active"|"very_active" }
Response 201:
  { "user": UserOut, "access_token": str, "token_type": "bearer" }
Errors: 409 email exists, 422 validation

POST /auth/login
Request:  { "email": str, "password": str }
Response: { "access_token": str, "token_type": "bearer" }
Errors: 401 invalid credentials

### Users

GET /users/me
Response: UserOut
  { "id": int, "email": str, "age": int, "weight_kg": float,
    "height_cm": float, "gender": str, "activity_level": str,
    "bmi": float, "tdee": int, "created_at": datetime }

PATCH /users/me
Request:  partial UserUpdate (any fields from UserOut except id, email, bmi, tdee)
Response: UserOut

### Goals

POST /goals
Request:
  { "goal_type": "weight_loss"|"muscle_gain"|"maintenance"|"health",
    "target_weight_kg": float|null,
    "daily_calories_kcal": int|null,
    "deadline": date|null }
Response 201: GoalOut { "id": int, ...fields, "is_active": true }

GET /goals/active
Response: GoalOut | null

### Nutrition logs

POST /nutrition/logs
Request:
  { "meal_type": "breakfast"|"lunch"|"dinner"|"snack",
    "food_name": str,
    "weight_g": float,
    "calories_kcal": float,
    "protein_g": float,
    "carbs_g": float,
    "fat_g": float,
    "logged_at": datetime|null  (null = now) }
Response 201: NutritionLogOut

GET /nutrition/logs
Query params: date=YYYY-MM-DD (default today), days=1..30
Response: { "logs": [NutritionLogOut], "summary": DaySummary }
  DaySummary: { "total_calories": float, "total_protein": float,
                "total_carbs": float, "total_fat": float,
                "goal_calories": int|null, "deficit_surplus": float|null }

DELETE /nutrition/logs/{log_id}
Response 204

### AI

POST /ai/chat
Request:  { "message": str }
Response: { "answer": str, "recommendation_id": int }
Note: non-streaming, for simple questions

POST /ai/chat/stream
Request:  { "message": str }
Response: text/event-stream (SSE)
  data: <text chunk>\n\n
  data: [DONE]\n\n
Note: use this for main chat UI

GET /ai/recommendations
Query: limit=20, offset=0
Response: { "items": [RecommendationOut], "total": int }

### Restrictions

POST /users/me/restrictions
Request:  { "type": "dietary"|"medical"|"allergy", "value": str }
Response 201: RestrictionOut

GET /users/me/restrictions
Response: [RestrictionOut]

DELETE /users/me/restrictions/{restriction_id}
Response 204

## Error response format (всегда одинаковый)
{ "detail": str, "code": str|null }
Examples:
  { "detail": "Email already registered", "code": "EMAIL_EXISTS" }
  { "detail": "Invalid credentials", "code": "AUTH_FAILED" }

## Pagination (где применяется)
{ "items": [...], "total": int, "limit": int, "offset": int }