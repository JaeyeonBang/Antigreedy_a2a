"""T6 Phase B: the FastAPI dashboard. A WebSocket connection triggers an A/B run
and streams every event live; a final {"type": "done"} closes the stream. The
index route serves the static A/B theater HTML.
"""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import create_app
from antigreedy.dashboard.runner import ABConfig


def _app():
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=220, max_rounds=6))


def test_ws_streams_both_conditions_then_done():
    client = TestClient(_app())
    received = []
    with client.websocket_connect("/ws") as ws:
        while True:
            ev = ws.receive_json()
            if ev.get("type") == "done":
                break
            received.append(ev)
    assert {e["condition"] for e in received} == {"baseline", "governed"}
    assert sum(1 for e in received if e["type"] == "episode_end") == 2
    assert any(e["type"] == "turn" for e in received)


def test_main_entry_wires_uvicorn(monkeypatch):
    import antigreedy.dashboard.__main__ as m
    calls = {}
    monkeypatch.setattr(m.uvicorn, "run",
                        lambda app, **kw: calls.update(kw, app=app))
    monkeypatch.setattr("sys.argv", ["antigreedy.dashboard", "--port", "9999"])
    m.main()
    assert calls["port"] == 9999 and calls["app"] is not None


def test_index_serves_html():
    client = TestClient(_app())
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    body = r.text.lower()
    assert "baseline" in body and "governed" in body  # the two panels
