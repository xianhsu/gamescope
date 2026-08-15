from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    type: str
    base_url: str | None = None
    reliability_level: str
