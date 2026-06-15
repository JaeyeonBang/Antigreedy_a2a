"""Configurable commons budget: the WS first message can carry `budget` so the
presenter can dial scenario difficulty live (small budget → collapse, large →
survive). Clamped to a sane range."""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import _clamp_budget, create_app
from antigreedy.dashboard.runner import ABConfig


def _app():
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=1200, max_rounds=4))


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


def _gov_budget(events):
    starts = [e for e in events if e["type"] == "episode_start"
              and e["condition"] == "governed"]
    return starts[0]["data"]["budget"] if starts else None


def test_clamp_budget():
    assert _clamp_budget(500) == 500
    assert _clamp_budget(50) == 200       # floor
    assert _clamp_budget(999999) == 8000  # ceiling


def test_budget_applied():
    assert _gov_budget(_run_ws(TestClient(_app()),
                               {"mode": "ab", "governed": True, "budget": 600})) == 600


def test_budget_defaults_to_cfg():
    assert _gov_budget(_run_ws(TestClient(_app()),
                               {"mode": "ab", "governed": True})) == 1200
