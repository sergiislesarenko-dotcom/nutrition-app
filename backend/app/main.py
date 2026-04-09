from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.routers.ai_router import router as ai_router
from app.routers.auth_router import router as auth_router
from app.routers.nutrition_router import router as nutrition_router
from app.routers.user_router import router as user_router

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="Nutrition App API",
    version="1.0.0",
    docs_url=f"{API_V1_PREFIX}/docs",
    redoc_url=f"{API_V1_PREFIX}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(user_router, prefix=API_V1_PREFIX)
app.include_router(nutrition_router, prefix=API_V1_PREFIX)
app.include_router(ai_router, prefix=API_V1_PREFIX)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Serialize AppError into the standard { detail, code } error shape."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.get(f"{API_V1_PREFIX}/health")
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok"}
