from antigreedy.governance import AgentAction, Policy, PolicyChain, SharedState, Verdict


class _Allow(Policy):
    name, priority = "allow", 100
    def evaluate(self, a, s, h): return self.allow()

class _Deny(Policy):
    name, priority = "deny", 10
    def evaluate(self, a, s, h): return self.deny(reason="nope")

class _Trunc(Policy):
    name, priority = "trunc", 20
    def evaluate(self, a, s, h):
        return self.modify({**a.payload, "content": "short"}, reason="t")

class _Flag(Policy):
    name, priority = "flag", 5
    def evaluate(self, a, s, h): return self.allow(flags={"suspicious": True})

class _Delay(Policy):
    name, priority = "delay", 15
    def evaluate(self, a, s, h): return self.delay(1.0, reason="wait")


def _a(): return AgentAction(agent_id="x", payload={"content": "long original"})

def test_allow_passes():
    assert PolicyChain([_Allow()]).evaluate(_a(), SharedState()).verdict == Verdict.ALLOW

def test_deny_short_circuits():
    r = PolicyChain([_Deny(), _Trunc()]).evaluate(_a(), SharedState())
    assert r.verdict == Verdict.DENY and r.reason == "nope"

def test_delay_short_circuits():
    r = PolicyChain([_Delay(), _Trunc()]).evaluate(_a(), SharedState())
    assert r.verdict == Verdict.DELAY and r.delay_seconds == 1.0

def test_modify_propagates():
    r = PolicyChain([_Trunc(), _Allow()]).evaluate(_a(), SharedState())
    assert r.verdict == Verdict.MODIFY and r.modified_payload["content"] == "short"

def test_flags_accumulate_without_blocking():
    r = PolicyChain([_Flag(), _Allow()]).evaluate(_a(), SharedState())
    assert r.verdict == Verdict.ALLOW and r.flags["suspicious"] is True

def test_priority_ordering():
    assert PolicyChain([_Trunc(), _Deny()]).evaluate(_a(), SharedState()).verdict == Verdict.DENY

def test_shared_state_dual_accounting():
    s = SharedState(commons={"token_budget_remaining": 1000})
    s.record_turn("a1", attempted=400, delivered=250)
    assert s.commons["token_budget_remaining"] == 750
    assert s.airtime_attempted["a1"] == 400 and s.airtime_delivered["a1"] == 250
