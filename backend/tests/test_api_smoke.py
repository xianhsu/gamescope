"""Hermetic API tests that do NOT touch the database.

They exercise the app wiring: routing, the root endpoint, request-id headers, the unified
error envelope, and request validation (which runs before any DB dependency resolves).
DB-backed endpoints are validated in CI against a real Postgres via migrate+seed.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestAppWiring:
    @pytest.mark.asyncio
    async def test_root_ok(self):
        async with await _client() as ac:
            resp = await ac.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"]
        assert body["docs"] == "/api/docs"

    @pytest.mark.asyncio
    async def test_request_id_header_present(self):
        async with await _client() as ac:
            resp = await ac.get("/")
        assert resp.headers.get("X-Request-ID")

    @pytest.mark.asyncio
    async def test_request_id_echoed_when_supplied(self):
        async with await _client() as ac:
            resp = await ac.get("/", headers={"X-Request-ID": "test-rid-123"})
        assert resp.headers.get("X-Request-ID") == "test-rid-123"

    @pytest.mark.asyncio
    async def test_unknown_route_404(self):
        async with await _client() as ac:
            resp = await ac.get("/api/v1/does-not-exist")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_error_uses_unified_envelope(self):
        # page must be >= 1 → validation fails before the DB dependency is used.
        async with await _client() as ac:
            resp = await ac.get("/api/v1/news", params={"page": 0})
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "INVALID_REQUEST"
        assert body["error"]["request_id"]

    @pytest.mark.asyncio
    async def test_openapi_schema_served(self):
        async with await _client() as ac:
            resp = await ac.get("/api/openapi.json")
        assert resp.status_code == 200
        assert resp.json()["info"]["title"]
