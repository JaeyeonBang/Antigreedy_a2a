"""Configurable agent count: the dashboard can run a meeting with N agents
(the WS first message carries n_agents), clamped to a sensible range."""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import _agents, create_app
from antigreedy.dashboard.runner import ABConfig


def _app():
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=300, max_rounds=4))


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


def _gov_agents(events):
    starts = [e for e in events if e["type"] == "episode_start"
              and e["condition"] == "governed"]
    return starts[0]["data"]["agents"] if starts else []


def test_agents_helper_generates_letters():
    assert _agents(3) == ["A", "B", "C"]
    assert _agents(2) == ["A", "B"]
    assert _agents(1) == ["A", "B"]        # clamped up to the 2 minimum
    assert _agents(99) == list("ABCDEFGH")  # clamped to the 8 maximum


def test_n_agents_three():
    agents = _gov_agents(_run_ws(TestClient(_app()),
                                 {"mode": "ab", "governed": True, "n_agents": 3}))
    assert agents == ["A", "B", "C"]


def test_n_agents_defaults_to_four():
    agents = _gov_agents(_run_ws(TestClient(_app()), {"mode": "ab", "governed": True}))
    assert len(agents) == 4


def test_n_agents_clamped_high():
    agents = _gov_agents(_run_ws(TestClient(_app()),
                                 {"mode": "ab", "governed": True, "n_agents": 50}))
    assert len(agents) == 8
