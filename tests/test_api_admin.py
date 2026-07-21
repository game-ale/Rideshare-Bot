"""
API tests for the FastAPI Admin Dashboard endpoints.
Uses httpx AsyncClient to test against the live app with a test database.
"""
import pytest
import os
from httpx import AsyncClient, ASGITransport

# Override database to use test DB before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_rideshare.db"

from api.main import app
from database.db import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    """Initialize the test database before each test module."""
    await init_db()
    yield


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthCheck:
    """Test the root health check endpoint."""

    async def test_root_returns_ok(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "RideShare Admin API"

    async def test_root_has_version(self, client):
        response = await client.get("/")
        data = response.json()
        assert "version" in data


class TestStatsEndpoint:
    """Test the /admin/stats endpoint."""

    async def test_stats_returns_200(self, client):
        response = await client.get("/admin/stats")
        assert response.status_code == 200

    async def test_stats_has_required_fields(self, client):
        response = await client.get("/admin/stats")
        data = response.json()
        required_fields = [
            "total_drivers", "available_drivers", "total_riders",
            "total_rides", "completed_rides", "cancelled_rides",
            "active_rides", "avg_rating", "completion_rate"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    async def test_stats_values_are_numeric(self, client):
        response = await client.get("/admin/stats")
        data = response.json()
        assert isinstance(data["total_drivers"], int)
        assert isinstance(data["avg_rating"], (int, float))
        assert isinstance(data["completion_rate"], (int, float))


class TestDriversEndpoint:
    """Test the /admin/drivers endpoints."""

    async def test_drivers_list_returns_200(self, client):
        response = await client.get("/admin/drivers")
        assert response.status_code == 200

    async def test_drivers_returns_list(self, client):
        response = await client.get("/admin/drivers")
        data = response.json()
        assert isinstance(data, list)

    async def test_drivers_filter_by_status(self, client):
        response = await client.get("/admin/drivers?status=APPROVED")
        assert response.status_code == 200

    async def test_pending_drivers_endpoint(self, client):
        response = await client.get("/admin/drivers/pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_nonexistent_driver_returns_404(self, client):
        response = await client.get("/admin/drivers/999999999")
        assert response.status_code == 404


class TestRidersEndpoint:
    """Test the /admin/riders endpoints."""

    async def test_riders_list_returns_200(self, client):
        response = await client.get("/admin/riders")
        assert response.status_code == 200

    async def test_riders_returns_list(self, client):
        response = await client.get("/admin/riders")
        data = response.json()
        assert isinstance(data, list)

    async def test_nonexistent_rider_returns_404(self, client):
        response = await client.get("/admin/riders/999999999")
        assert response.status_code == 404


class TestRidesEndpoint:
    """Test the /admin/rides endpoints."""

    async def test_rides_list_returns_200(self, client):
        response = await client.get("/admin/rides")
        assert response.status_code == 200

    async def test_rides_filter_completed(self, client):
        response = await client.get("/admin/rides?status=COMPLETED")
        assert response.status_code == 200

    async def test_rides_filter_cancelled(self, client):
        response = await client.get("/admin/rides?status=CANCELLED")
        assert response.status_code == 200

    async def test_rides_limit_param(self, client):
        response = await client.get("/admin/rides?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    async def test_nonexistent_ride_returns_404(self, client):
        response = await client.get("/admin/rides/999999")
        assert response.status_code == 404


class TestAIEndpoints:
    """Test the AI insight and demand endpoints."""

    async def test_insights_returns_200(self, client):
        response = await client.get("/admin/ai/insights")
        assert response.status_code == 200

    async def test_insights_returns_list(self, client):
        response = await client.get("/admin/ai/insights")
        data = response.json()
        assert isinstance(data, list)

    async def test_demand_returns_200(self, client):
        response = await client.get("/admin/ai/demand")
        assert response.status_code == 200

    async def test_demand_has_forecast(self, client):
        response = await client.get("/admin/ai/demand")
        data = response.json()
        assert "forecast" in data
        assert "hotspots" in data
        assert "recommendation" in data
