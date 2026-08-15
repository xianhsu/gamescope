from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import ai, games, health, news, search, system, trending

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(news.router)
api_router.include_router(games.router)
api_router.include_router(search.router)
api_router.include_router(ai.router)
api_router.include_router(trending.router)
api_router.include_router(system.router)
