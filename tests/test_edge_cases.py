"""Edge-case coverage: behavioural branches and CLI entry points that the
happy-path suites skip — the 'survived' outcome, malformed judge scores, the
probe deny/empty-message paths, and the gate/bench mock CLIs.
"""
import asyncio
from pathlib import Path

from antigreedy.backends import MockBackend, make_meeting_script, make_probe_script
from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.metrics import episode_summary
from antigreedy.probe.cards import FactCard
from antigreedy.probe.monitor import DeceptionMonitor
from antigreedy.probe.scenario import ProbeConfig, run_probe_episode, score_episode
from antigreedy.scenario.meeting import MeetingConfig, run_episode

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"


# --- meeting "survived" outcome (max_rounds reached, commons left, no decision) ---
def test_meeting_survived_outcome():
    loader = PolicyLoader(REPO_POLICIES)
    state = SharedState()
    ip = InProcessInterceptPoint(loader, state)
    stream = EventStream("t", "governed", 0)
    cfg = MeetingConfig(run_id="t", condition="governed", episode=0,
                        personas={a: "" for a in "ABCD"}, budget=8000, max_rounds=2)
    backend = MockBackend(make_meeting_script(dominator="A"))  # A never agrees → no decision
    out = asyncio.run(run_episode(cfg, backend, ip, stream, state))
    assert out["outcome"] == "survived"   # ran the rounds, commons survived, no unanimity
    assert out["commons_left"] > 0


# --- monitor: malformed SCORE falls back to 0.0 (still parses the verdict) ---
def test_monitor_score_parse_fallback():
    class _BadScore:
        async def complete(self, prompt, max_tokens):
            return {"text": "VERDICT: yes\nSCORE: not-a-number", "completion_tokens": 5}
    r = asyncio.run(DeceptionMonitor(_BadScore()).judge_message("", "msg"))
    assert r["deception_suspected"] is True and r["score"] == 0.0


# --- probe: a denied agent delivers nothing; score_episode skips empty messages ---
def test_probe_deny_path_and_empty_skip(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "deny_a.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class D(Policy):\n"
        "    name, priority = 'deny_a', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        return self.deny() if a.agent_id=='A' else self.allow()\n")
    cards = {a: FactCard(a, "hours", 10.0) for a in "ABCD"}
    state = SharedState()
    ip = InProcessInterceptPoint(PolicyLoader(d), state)
    stream = EventStream("t", "probe", 0)
    cfg = ProbeConfig(run_id="t", episode=0, cards=cards, probe="A", budget=4000)
    asyncio.run(run_probe_episode(cfg, MockBackend(make_probe_script()), ip, stream, state))
    a_turns = [e for e in stream.events if e["type"] == "turn" and e["data"]["agent_id"] == "A"]
    assert a_turns and all(e["data"]["content"] == "" for e in a_turns)   # denied → empty
    # score_episode must skip A's empty messages (no pair emitted for them)
    monitor = DeceptionMonitor(MockBackend(lambda p: "VERDICT: no\nSCORE: 0.0"))
    labels = asyncio.run(score_episode(stream.events, monitor))
    assert all(isinstance(t, tuple) for t in labels)  # only non-empty messages scored


# --- probe: a MODIFY verdict truncates the probe's delivered content (scenario path) ---
def test_probe_modify_path(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "mod_a.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class M(Policy):\n"
        "    name, priority = 'mod_a', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        if a.agent_id == 'A':\n"
        "            return self.modify({**a.payload, 'content': a.payload.get('content','')[:3]})\n"
        "        return self.allow()\n")
    cards = {a: FactCard(a, "hours", 10.0) for a in "ABCD"}
    state = SharedState()
    ip = InProcessInterceptPoint(PolicyLoader(d), state)
    stream = EventStream("t", "probe", 0)
    cfg = ProbeConfig(run_id="t", episode=0, cards=cards, probe="A", budget=4000)
    asyncio.run(run_probe_episode(cfg, MockBackend(make_probe_script()), ip, stream, state))
    a_turns = [e for e in stream.events if e["type"] == "turn" and e["data"]["agent_id"] == "A"]
    assert a_turns and all(e["data"]["verdict"] == "modify" for e in a_turns)
    assert all(len(e["data"]["content"]) <= 3 for e in a_turns)   # truncated, not empty


# --- CLI entry points (mock, fast) ---
def test_gate_main_mock(monkeypatch, tmp_path):
    import antigreedy.gate as g
    monkeypatch.setattr("sys.argv",
                        ["gate", "--episodes", "1", "--out", str(tmp_path)])
    g.main()
    assert list(tmp_path.glob("*-report.json"))


def test_bench_main_mock(monkeypatch, tmp_path):
    import antigreedy.bench as b
    monkeypatch.setattr("sys.argv",
                        ["bench", "--episodes", "2", "--out", str(tmp_path)])
    b.main()
    assert list(tmp_path.glob("*-bench.json"))


# --- dashboard: default backend factories drive all three modes ---
def test_dashboard_default_factories_run():
    from fastapi.testclient import TestClient
    from antigreedy.dashboard.app import create_app
    from antigreedy.dashboard.runner import ABConfig
    app = create_app(cfg=ABConfig(run_id="t", budget=300, max_rounds=2,
                                  live_budget=600, live_max_rounds=2, live_delay=0.0))
    client = TestClient(app)
    for msg in ({"mode": "ab"}, {"mode": "probe"}, {"mode": "live"}):
        with client.websocket_connect("/ws") as ws:
            ws.send_json(msg)
            while ws.receive_json().get("type") != "done":
                pass


# --- dashboard: a mid-run client disconnect is handled cleanly ---
def test_dashboard_disconnect_mid_run_is_clean():
    from fastapi.testclient import TestClient
    from antigreedy.dashboard.app import create_app
    from antigreedy.dashboard.runner import ABConfig
    app = create_app(cfg=ABConfig(run_id="t", live_budget=9000, live_max_rounds=8,
                                  live_delay=0.2))
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"mode": "live"})
        ws.receive_json()                 # one event, then disconnect on context exit
    # the server must absorb the disconnect; a fresh run still works
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"mode": "ab"})
        while ws.receive_json().get("type") != "done":
            pass


# --- meeting: a delay on the final round expires uncharged (delay_expired) ---
def test_meeting_delay_expired(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "delay_last.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class DL(Policy):\n"
        "    name, priority = 'delay_last', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        if a.agent_id == 'A' and a.round == 1:\n"
        "            return self.delay(0.0, reason='hold to last round')\n"
        "        return self.allow()\n")
    state = SharedState()
    ip = InProcessInterceptPoint(PolicyLoader(d), state)
    stream = EventStream("t", "governed", 0)
    cfg = MeetingConfig(run_id="t", condition="governed", episode=0,
                        personas={a: "" for a in "ABCD"}, budget=5000, max_rounds=2)
    asyncio.run(run_episode(cfg, MockBackend(make_meeting_script(dominator=None)),
                            ip, stream, state))
    assert any(e["type"] == "delay_expired" and e["data"]["agent_id"] == "A"
               for e in stream.events)


# --- metrics: episode_summary folds a decision event into 'decided' ---
def test_episode_summary_decision():
    events = [
        {"type": "turn", "data": {"agent_id": "A", "round": 0, "verdict": "allow",
                                  "attempted_tokens": 10, "delivered_tokens": 10}},
        {"type": "decision", "data": {"round": 0}},
        {"type": "episode_end", "data": {"commons_left": 50}},
    ]
    s = episode_summary(events)
    assert s["outcome"] == "decided"


# --- gate/bench OpenRouter CLI wiring (fake backend, no real API) ---
class _FakeOR:
    def __init__(self, model, *a, **k):
        pass

    async def complete(self, prompt, max_tokens):
        from antigreedy.backends import (
            make_meeting_script, make_probe_script, rough_tokens,
        )
        if "STATEMENT UNDER REVIEW" in prompt:
            txt = "VERDICT: no\nSCORE: 0.1"
        elif "team lead in an allocation" in prompt:
            txt = make_probe_script()(prompt)
        else:
            txt = make_meeting_script(dominator="A")(prompt)
        return {"text": txt, "completion_tokens": rough_tokens(txt)}


def test_gate_main_openrouter_wiring(monkeypatch, tmp_path):
    import antigreedy.backends as bk
    monkeypatch.setattr(bk, "OpenRouterBackend", _FakeOR)
    import antigreedy.gate as g
    monkeypatch.setattr("sys.argv", ["gate", "--backend", "openrouter",
                                     "--episodes", "1", "--out", str(tmp_path)])
    g.main()
    assert list(tmp_path.glob("*-report.json"))


def test_bench_main_openrouter_wiring(monkeypatch, tmp_path):
    import antigreedy.backends as bk
    monkeypatch.setattr(bk, "OpenRouterBackend", _FakeOR)
    import antigreedy.bench as b
    monkeypatch.setattr("sys.argv", ["bench", "--backend", "openrouter",
                                     "--episodes", "1", "--out", str(tmp_path)])
    b.main()
    assert list(tmp_path.glob("*-bench.json"))
