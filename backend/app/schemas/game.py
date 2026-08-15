from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    developer: str | None = None
    publisher: str | None = None
    release_date: date | None = None


class GameWithCount(GameOut):
    article_count: int = 0
