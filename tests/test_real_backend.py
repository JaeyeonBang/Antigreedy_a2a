"""Real-LLM toggle: the dashboard can run with a real backend (OpenRouter) when
one is configured. The WS first message carries `backend: "real"`; GET /config
tells the UI whether a real backend is available (so it can warn about API cost
and disable the option when no key is set)."""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import create_app
from antigreedy.dashboard.runner import ABConfig


def _marker_backend():
    # stands in for the "real" backend: every turn says REALMARKER
    return MockBackend(lambda prompt: "SPEAK: REALMARKER hello\nAGREE: yes\nBID: no")


def _app(real=True):
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        real_backend_factory=_marker_backend if real else None,
        cfg=ABConfig(run_id="t", budget=300, max_rounds=3))


def _run_ws(client, config):
    received = []
    with client.websocket_connect("/ws") as ws:
        ws.send_json(config)
        while True:
            ev = ws.receive_json()
            if ev.get("type") == "done":
                break
            received.append(ev)
    return received


def _gov_text(events):
    return " ".join(t["data"].get("original_text", "") for t in events
                    if t["type"] == "turn" and t["condition"] == "governed")


def test_config_reports_real_available():
    assert TestClient(_app(real=True)).get("/config").json()["real_available"] is True
    assert TestClient(_app(real=False)).get("/config").json()["real_available"] is False


def test_backend_real_uses_real_factory():
    events = _run_ws(TestClient(_app(real=True)),
                     {"mode": "ab", "governed": True, "backend": "real"})
    assert "REALMARKER" in _gov_text(events)


def test_backend_mock_does_not_use_real():
    events = _run_ws(TestClient(_app(real=True)),
                     {"mode": "ab", "governed": True, "backend": "mock"})
    assert "REALMARKER" not in _gov_text(events)


def test_real_requested_but_unavailable_falls_back_to_mock():
    # no real factory configured → request for real must not crash; runs on mock
    events = _run_ws(TestClient(_app(real=False)),
                     {"mode": "ab", "governed": True, "backend": "real"})
    assert any(e["type"] == "turn" for e in events)
    assert "REALMARKER" not in _gov_text(events)
