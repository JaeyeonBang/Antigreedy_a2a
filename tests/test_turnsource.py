"""TurnSource seam (T5 Phase 1): the per-turn execution mechanism extracted from
the meeting loop, so the SAME round/decision/charging orchestration runs over
either the in-process intercept or an A2A transport. ``InProcessTurnSource``
reproduces the meeting's original turn logic exactly.
"""
import asyncio
from pathlib import Path

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState, Verdict
from antigreedy.protocol import build_prompt
from antigreedy.turnsource import InProcessTurnSource, TurnResult

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"
TOPIC = "Allocate the shared compute budget."


def _source(policy_dir, state, dominator="A", max_tokens=300):
    ip = InProcessInterceptPoint(PolicyLoader(policy_dir), state)
    backend = MockBackend(make_meeting_script(dominator=dominator))
    return InProcessTurnSource(backend, ip, max_tokens=max_tokens)


def _prompt(agent, round_no=0, budget=400):
    return build_prompt(agent, "", TOPIC, "", round_no, budget)


def _take(source, agent="A", round_no=0, budget=400):
    return asyncio.run(source.take(agent, round_no, _prompt(agent, round_no, budget)))


def test_take_allow_passes_speak_through(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    tr = _take(_source(d, SharedState(), dominator=None), agent="B")
    assert isinstance(tr, TurnResult)
    assert tr.verdict is Verdict.ALLOW
    assert tr.delivered_text == tr.original_text and tr.delivered_text
    assert tr.attempted_tokens > 0
    assert tr.agree in (True, False) and tr.parse_ok


def test_take_deny_yields_empty_delivery(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "deny_a.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class D(Policy):\n"
        "    name, priority = 'deny_a', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        return self.deny() if a.agent_id=='A' else self.allow()\n")
    tr = _take(_source(d, SharedState()), agent="A")
    assert tr.verdict is Verdict.DENY
    assert tr.delivered_text == ""
    assert tr.original_text  # the agent did try to speak


def test_take_modify_truncates_but_keeps_original(tmp_path):
    state = SharedState()
    state.commons.update(token_budget_remaining=400, token_budget_total=400, n_agents=4)
    tr = _take(_source(REPO_POLICIES, state), agent="A")
    assert tr.verdict is Verdict.MODIFY
    assert 0 < len(tr.delivered_text) < len(tr.original_text)
    # chain aggregates MODIFY → reports "chain"; airtime_quota's flag still rides along
    assert tr.policy_name == "chain"
    assert tr.flags.get("airtime_greedy") is True


def test_take_delay_holds_delivery(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "delay_a.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class DelayA(Policy):\n"
        "    name, priority = 'delay_a', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        return self.delay(0.0) if a.agent_id=='A' else self.allow()\n")
    tr = _take(_source(d, SharedState()), agent="A")
    assert tr.verdict is Verdict.DELAY
    assert tr.delivered_text == ""
    assert tr.original_text  # preserved for re-delivery by the orchestrator


def test_policy_set_hash_exposed(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    src = _source(d, SharedState())
    assert isinstance(src.policy_set_hash(), str) and len(src.policy_set_hash()) >= 8
