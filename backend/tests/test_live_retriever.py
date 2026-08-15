"""Unit tests for the live web retriever (SerpAPI).

Network and the SerpAPI key are never touched — httpx is mocked so the tests run anywhere.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core import config as config_mod
from app.retrieval import live as live_mod
from app.retrieval.base import RetrievalFilters


@pytest.fixture
def serpapi_settings(monkeypatch):
    monkeypatch.setattr(config_mod.settings, "live_retrieval_provider", "serpapi")
    monkeypatch.setattr(config_mod.settings, "serpapi_api_key", "test-key")
    yield config_mod.settings


def test_factory_returns_serpapi_when_configured(serpapi_settings):
    assert isinstance(live_mod.get_live_retriever(), live_mod.SerpAPILiveRetriever)


def test_factory_returns_null_when_provider_null(monkeypatch):
    monkeypatch.setattr(config_mod.settings, "live_retrieval_provider", "null")
    monkeypatch.setattr(config_mod.settings, "serpapi_api_key", "test-key")
    assert isinstance(live_mod.get_live_retriever(), live_mod.NullLiveRetriever)


def test_factory_returns_null_when_key_missing(monkeypatch):
    monkeypatch.setattr(config_mod.settings, "live_retrieval_provider", "serpapi")
    monkeypatch.setattr(config_mod.settings, "serpapi_api_key", "")
    assert isinstance(live_mod.get_live_retriever(), live_mod.NullLiveRetriever)


async def test_serpapi_parses_organic_results(serpapi_settings):
    sample = {
        "organic_results": [
            {
                "title": "Elden Ring DLC announced",
                "link": "https://example.com/a",
                "source": "IGN",
                "snippet": "Latest details revealed.",
            },
            {"title": "No link result", "snippet": "should be skipped"},
        ]
    }

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return sample

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            return _Resp()

    with patch.object(live_mod.httpx, "AsyncClient", lambda *a, **k: _Client()):
        retriever = live_mod.SerpAPILiveRetriever(api_key="test-key")
        docs = await retriever.retrieve("elden ring news", RetrievalFilters(), 5)

    assert len(docs) == 1
    d = docs[0]
    assert d.article_id == 0
    assert d.retriever == "live"
    assert d.external["url"] == "https://example.com/a"
    assert d.external["title"] == "Elden Ring DLC announced"
    assert d.external["snippet"] == "Latest details revealed."
    assert d.external["source"] == "IGN"


async def test_serpapi_returns_empty_on_http_error(serpapi_settings):
    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            raise live_mod.httpx.ConnectError("boom")

    with patch.object(live_mod.httpx, "AsyncClient", lambda *a, **k: _Client()):
        retriever = live_mod.SerpAPILiveRetriever(api_key="test-key")
        docs = await retriever.retrieve("x", RetrievalFilters(), 5)

    assert docs == []
