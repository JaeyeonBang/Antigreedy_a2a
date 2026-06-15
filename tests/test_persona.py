"""Editable agent personas: the WS first message can carry `personas` (per-agent
text) which flows into each agent's prompt. Lets the presenter give an agent a
personality from the dashboard (visible in the prompt; behaviour changes under a
real LLM)."""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import create_app
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


def test_persona_flows_into_prompt():
    events = _run_ws(TestClient(_app()),
                     {"mode": "ab", "governed": True, "n_agents": 2,
                      "personas": {"A": "PERSONA_MARKER_XYZ wants all the airtime"}})
    a_turns = [e for e in events if e["type"] == "turn"
               and e["condition"] == "governed" and e["data"]["agent_id"] == "A"]
    assert a_turns
    assert any("PERSONA_MARKER_XYZ" in t["data"]["prompt"] for t in a_turns)
    # an agent with no persona set is unaffected
    b_turns = [e for e in events if e["type"] == "turn"
               and e["condition"] == "governed" and e["data"]["agent_id"] == "B"]
    assert b_turns and all("PERSONA_MARKER_XYZ" not in t["data"]["prompt"] for t in b_turns)


def test_personas_default_empty():
    events = _run_ws(TestClient(_app()), {"mode": "ab", "governed": True, "n_agents": 2})
    turns = [e for e in events if e["type"] == "turn"]
    assert turns  # runs fine with no personas supplied
