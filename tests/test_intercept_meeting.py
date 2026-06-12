"""InterceptPoint contract + meeting charging/DECISION/cap semantics (P1 set)."""
import asyncio
from pathlib import Path

import pytest

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.events import EventStream
from antigreedy.governance import AgentAction, SharedState, Verdict
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.metrics import episode_summary
from antigreedy.scenario.meeting import MeetingConfig, run_episode

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"


# --- InterceptPoint contract suite (eng decision 1): run against ANY impl ---
def intercept_contract(make_intercept):
    async def run():
        ip, state = make_intercept()
        r = await ip.submit(AgentAction(agent_id="A", token_estimate=10_000,
                                        payload={"content": "x" * 40_000}))
        assert r.verdict in (Verdict.MODIFY, Verdict.DENY, Verdict.ALLOW, Verdict.DELAY)
        assert isinstance(ip.policy_set_hash(), str) and len(ip.policy_set_hash()) >= 8
    asyncio.run(run())

def test_inprocess_intercept_contract():
    def mk():
        state = SharedState(commons={"token_budget_remaining": 1000})
        return InProcessInterceptPoint(PolicyLoader(REPO_POLICIES), state), state
    intercept_contract(mk)


def _run(policy_dir, budget=300, max_rounds=4, dominator="A", cap=20000):
    loader = PolicyLoader(policy_dir)
    state = SharedState()
    ip = InProcessInterceptPoint(loader, state)
    stream = EventStream("t", "governed" if str(policy_dir).endswith("policies") else "baseline", 0)
    personas = {a: "" for a in ["A", "B", "C", "D"]}
    cfg = MeetingConfig(run_id="t", condition=stream.condition, episode=0,
                        personas=personas, budget=budget, max_rounds=max_rounds,
                        safety_cap=cap)
    backend = MockBackend(make_meeting_script(dominator=dominator))
    out = asyncio.run(run_episode(cfg, backend, ip, stream, state))
    return out, stream.events, state


def test_charging_allow_full_and_modify_truncated(tmp_path):
    # governed: quota truncates dominator → delivered < attempted for A
    _, events, _ = _run(REPO_POLICIES, budget=400)
    s = episode_summary(events)
    assert s["delivered"]["A"] < s["attempted"]["A"] * 0.6    # modify charged truncated
    # allow charges the SPEAK content; per-turn protocol-line overhead is the only gap
    b_turns = [e["data"] for e in events
               if e["type"] == "turn" and e["data"]["agent_id"] == "B"]
    assert b_turns and all(d["verdict"] == "allow" for d in b_turns)
    assert all(d["attempted_tokens"] - 10 <= d["delivered_tokens"] <= d["attempted_tokens"]
               for d in b_turns)

def test_charging_deny_is_zero(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "deny_a.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class D(Policy):\n"
        "    name, priority = 'deny_dom', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        return self.deny(reason='gag') if a.agent_id=='A' else self.allow()\n")
    _, events, _ = _run(d, budget=400)
    s = episode_summary(events)
    assert s["delivered"].get("A", 0) == 0 and s["attempted"]["A"] > 0

def test_decision_when_all_agree(tmp_path):
    # No dominator → everyone agrees from round 3 → DECISION
    d = tmp_path / "empty"; d.mkdir()
    out, events, _ = _run(d, budget=5000, max_rounds=8, dominator=None)
    assert out["outcome"] == "decided"
    assert any(e["type"] == "decision" for e in events)

def test_collapse_on_exhaustion(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    out, _, _ = _run(d, budget=150, max_rounds=8, dominator="A")
    assert out["outcome"] == "exhausted"

def test_cap_aborted_distinct_from_exhaustion(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    out, _, _ = _run(d, budget=10_000, max_rounds=8, dominator="A", cap=300)
    assert out["outcome"] == "cap_aborted"

def test_extra_turn_bid_max_one_per_round(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    _, events, _ = _run(d, budget=2000, max_rounds=1, dominator="A")
    extras = [e for e in events if e["type"] == "turn" and e["data"]["extra"]]
    assert len([e for e in extras if e["data"]["agent_id"] == "A"]) <= 1
    assert len(extras) >= 1  # dominator did get its extra turn

def test_envelope_on_all_events(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    _, events, _ = _run(d, budget=300)
    for ev in events:
        assert {"run_id", "condition", "episode", "seq", "schema_version"} <= set(ev)
    turn_evs = [e for e in events if e["type"] == "turn"]
    assert all("policy_set_hash" in e for e in turn_evs)
