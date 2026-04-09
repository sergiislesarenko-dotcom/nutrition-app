from typing import AsyncGenerator

import pytest
import pytest_asyncio

# All async tests in this directory use the session-scoped event loop so that
# aiomysql connections (created inside async fixtures) are not attached to a
# different loop than the running test coroutine.
pytestmark = pytest.mark.asyncio(loop_scope="session")
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.core.dependencies import get_db
from app.main import app

test_engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session")
async def setup_test_db():
    """Create all tables once for the test session; drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


async def _truncate_all(engine) -> None:
    """Truncate every table in reverse FK order to reset state between tests."""
    async with engine.begin() as conn:
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Yield a real async session; truncate tables after each test."""
    async with TestAsyncSessionLocal() as session:
        yield session
    await _truncate_all(test_engine)


@pytest_asyncio.fixture(scope="function")
async def client(setup_test_db) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client wired to the test DB; truncates tables after each test."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Provide a fresh test session for each request."""
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
    await _truncate_all(test_engine)


@pytest.fixture
def user_payload() -> dict:
    """Valid user registration payload."""
    return {
        "email": "testuser@example.com",
        "password": "securepass123",
        "age": 25,
        "weight_kg": 70.0,
        "height_cm": 175.0,
        "gender": "male",
        "activity_level": "moderate",
    }


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient, user_payload: dict) -> dict:
    """Register a test user and return the full auth response JSON."""
    response = await client.post("/api/v1/auth/register", json=user_payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(registered_user: dict) -> dict:
    """Return Authorization headers for the registered test user."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}
