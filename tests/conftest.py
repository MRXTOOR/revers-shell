"""Pytest configuration and fixtures."""
import pytest
import fakeredis
from app.main import create_app
from app.redis_client import RedisClient
from app import routes


@pytest.fixture
def fake_redis():
    """Create fake Redis client for testing."""
    server = fakeredis.FakeStrictRedis(decode_responses=True)
    yield server
    # Cleanup: flush all data
    server.flushall()


@pytest.fixture
def redis_client_instance(fake_redis):
    """Create RedisClient instance for testing with fake Redis."""
    client = RedisClient(redis_client=fake_redis)
    yield client


@pytest.fixture
def app(fake_redis):
    """Create Flask application for testing."""
    # Replace the global redis_client in routes with a test instance using fake Redis
    test_redis_client = RedisClient(redis_client=fake_redis)
    original_redis_client = routes.redis_client
    routes.redis_client = test_redis_client
    
    app = create_app()
    app.config['TESTING'] = True
    
    yield app
    
    # Restore original redis_client
    routes.redis_client = original_redis_client


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

