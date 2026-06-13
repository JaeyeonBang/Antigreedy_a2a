"""One-touch live governance: a single meeting whose governance can be switched
ON/OFF mid-run with one click. LiveInterceptPoint flips between the governed and
empty policy sets instantly (single-writer: only the orchestrator/control flips
it), so applying governance takes effect on the very next turn.
"""
import asyncio
from pathlib import Path

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.live import LiveInterceptPoint, make_live
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import AgentAction, SharedState, Verdict

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"


def _big_action():
    return AgentAction(agent_id="A", token_estimate=10_000,
                       payload={"content": "x" * 40_000})


def test_live_intercept_off_allows_on_governs(tmp_path):
    empty = tmp_path / "empty"; empty.mkdir()
    state = SharedState(commons={"token_budget_remaining": 1000,
                                 "token_budget_total": 1000, "n_agents": 4})
    lip = LiveInterceptPoint(PolicyLoader(REPO_POLICIES), PolicyLoader(empty), state)

    # governance OFF → ungoverned (allow even a huge greedy turn)
    assert lip.governance_on is False
    off = asyncio.run(lip.submit(_big_action()))
    assert off.verdict is Verdict.ALLOW

    # one-touch: flip ON → the SAME action is now governed (truncated/denied)
    lip.governance_on = True
    on = asyncio.run(lip.submit(_big_action()))
    assert on.verdict in (Verdict.MODIFY, Verdict.DENY)

    assert isinstance(lip.policy_set_hash(), str) and len(lip.policy_set_hash()) >= 8


def _live_client(**cfgkw):
    from fastapi.testclient import TestClient
    from antigreedy.dashboard.app import create_app
    from antigreedy.dashboard.runner import ABConfig
    return TestClient(create_app(cfg=ABConfig(run_id="t", **cfgkw)))


def _drain(ws):
    out = []
    while True:
        ev = ws.receive_json()
        if ev.get("type") == "done":
            return out
        out.append(ev)


def test_ws_live_default_is_ungoverned():
    client = _live_client(live_budget=600, live_max_rounds=4, live_delay=0.0)
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"mode": "live"})          # no control → governance stays off
        received = _drain(ws)
    turns = [e for e in received if e["type"] == "turn"]
    assert turns and all(t["data"]["verdict"] == "allow" for t in turns)


def test_ws_live_one_touch_apply_governs():
    client = _live_client(live_budget=3000, live_max_rounds=8, live_delay=0.1)
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"mode": "live"})
        ws.send_json({"action": "govern_on"})   # one-touch apply mid-run
        received = _drain(ws)
    turns = [e for e in received if e["type"] == "turn"]
    assert any(t["data"]["verdict"] in ("modify", "deny") for t in turns)


def test_make_live_builds_paced_source(tmp_path):
    empty = tmp_path / "empty"; empty.mkdir()
    backend = MockBackend(make_meeting_script(dominator="A"))
    lip, src, state = make_live(REPO_POLICIES, empty, backend, delay=0.0)
    assert lip.governance_on is False
    from antigreedy.protocol import build_prompt
    state.commons.update(token_budget_remaining=1000, token_budget_total=1000, n_agents=4)
    tr = asyncio.run(src.take("A", 0, build_prompt("A", "", "topic", "", 0, 1000)))
    assert tr.verdict is Verdict.ALLOW          # governance off → allowed
    lip.governance_on = True
    tr2 = asyncio.run(src.take("A", 0, build_prompt("A", "", "topic", "", 0, 1000)))
    assert tr2.verdict in (Verdict.MODIFY, Verdict.DENY)  # one-touch applied
