from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.repositories.game_repo import GameRepository
from app.schemas.game import GameOut, GameWithCount


class GameService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = GameRepository(db)

    async def list_games(self) -> list[GameOut]:
        rows, _ = await self.repo.list(limit=200)
        return [GameOut.model_validate(g) for g in rows]

    async def get_game(self, slug: str) -> GameWithCount:
        game = await self.repo.get_by_slug(slug)
        if game is None:
            raise NotFoundError(f"Game '{slug}' not found.")
        count = await self.repo.article_count(game.id)
        out = GameWithCount.model_validate(game)
        out.article_count = count
        return out

    async def trending(self, limit: int = 8) -> list[GameWithCount]:
        pairs = await self.repo.trending(limit=limit)
        result: list[GameWithCount] = []
        for game, count in pairs:
            out = GameWithCount.model_validate(game)
            out.article_count = count
            result.append(out)
        # Fallback: if there is not enough recent activity, show any games so the UI isn't empty.
        if len(result) < limit:
            existing = {g.id for g in result}
            rows, _ = await self.repo.list(limit=limit)
            for g in rows:
                if g.id not in existing:
                    result.append(GameWithCount.model_validate(g))
                if len(result) >= limit:
                    break
        return result
