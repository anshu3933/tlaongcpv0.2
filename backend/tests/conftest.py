import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from auth_service.src.main import app
from auth_service.src.database import get_async_session
from auth_service.src.models.base import Base
from auth_service.src.models.user import User
from auth_service.src.security import hash_password

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with test database"""
    async def override_get_async_session():
        yield test_session
    
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        role="user",
        is_active=True,
        is_superuser=False
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user

@pytest.fixture
async def test_superuser(test_session: AsyncSession) -> User:
    """Create a test superuser"""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        full_name="Admin User",
        role="admin",
        is_active=True,
        is_superuser=True
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user

@pytest.fixture
async def user_token(client: AsyncClient, test_user: User) -> str:
    """Get authentication token for test user"""
    response = await client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
async def superuser_token(client: AsyncClient, test_superuser: User) -> str:
    """Get authentication token for test superuser"""
    response = await client.post(
        "/auth/login",
        json={
            "email": test_superuser.email,
            "password": "adminpassword123"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """Get authorization headers for test user"""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def admin_headers(superuser_token: str) -> dict:
    """Get authorization headers for test superuser"""
    return {"Authorization": f"Bearer {superuser_token}"}