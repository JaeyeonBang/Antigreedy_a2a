import asyncio
import pytest
import httpx
from antigreedy import backends
from antigreedy.backends import OpenRouterBackend


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        OpenRouterBackend("m", api_key=None)


class _FakeResp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("e", request=httpx.Request("POST", "http://x"),
                                        response=httpx.Response(self.status_code))

    def json(self):
        return self._body


def _client_factory(responses):
    seq = iter(responses)

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, headers=None):
            return next(seq)

    return _FakeClient


_OK_BODY = {"choices": [{"message": {"content": "hello world"}}],
            "usage": {"completion_tokens": 7}}


def test_success_path(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _client_factory([_FakeResp(200, _OK_BODY)]))
    b = OpenRouterBackend("m", api_key="k", max_retries=1)
    r = asyncio.run(b.complete("p", 50))
    assert r["text"] == "hello world" and r["completion_tokens"] == 7


def test_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient",
                        _client_factory([_FakeResp(429, {}), _FakeResp(200, _OK_BODY)]))
    monkeypatch.setattr(backends.asyncio, "sleep", lambda *_a, **_k: _noop())
    b = OpenRouterBackend("m", api_key="k", max_retries=3)
    r = asyncio.run(b.complete("p", 50))
    assert r["completion_tokens"] == 7


async def _noop():
    return None


def test_exhausts_retries_raises(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient",
                        _client_factory([_FakeResp(500, {}), _FakeResp(503, {})]))
    monkeypatch.setattr(backends.asyncio, "sleep", lambda *_a, **_k: _noop())
    b = OpenRouterBackend("m", api_key="k", max_retries=2)
    with pytest.raises(RuntimeError):
        asyncio.run(b.complete("p", 50))
