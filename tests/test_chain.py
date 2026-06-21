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


class _CapTo(Policy):
    """content를 n글자로 자르고, 자르기 전에 *받은* 길이를 payload에 기록 → 체인 전파 증명용."""
    def __init__(self, n, prio):
        self.n, self.priority, self.name = n, prio, f"cap{n}"
    def evaluate(self, a, s, h):
        recv = len(a.payload.get("content", ""))
        return self.modify({**a.payload, "content": a.payload["content"][:self.n],
                            "_seen_len": recv}, reason=f"cap{self.n}",
                           flags={f"cut_{self.n}": True})


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

def test_two_modifies_both_cut_second_sees_first_output():
    """이중 컷: MODIFY 정책 2개가 모두 적용되고, 두 번째가 첫 번째의 *수정된* payload를
    본다(전파). content '0123456789'(10) → cap8 → cap4."""
    a = AgentAction(agent_id="x", payload={"content": "0123456789"})
    r = PolicyChain([_CapTo(8, 10), _CapTo(4, 20)]).evaluate(a, SharedState())
    assert r.verdict == Verdict.MODIFY
    assert r.modified_payload["content"] == "0123"          # 더 빡빡한 컷이 최종
    assert r.modified_payload["_seen_len"] == 8             # 두 번째가 첫 컷 결과(8)를 봄(원본 10 아님)
    assert r.flags == {"cut_8": True, "cut_4": True}        # 두 컷의 flags 누적


def test_two_modifies_order_independent_result_tighter_wins():
    """우선순위로 정렬되므로 입력 순서와 무관하게 같은 결과(더 빡빡한 컷이 이김)."""
    a = AgentAction(agent_id="x", payload={"content": "0123456789"})
    r1 = PolicyChain([_CapTo(4, 20), _CapTo(8, 10)]).evaluate(a, SharedState())
    r2 = PolicyChain([_CapTo(8, 10), _CapTo(4, 20)]).evaluate(a, SharedState())
    assert r1.modified_payload["content"] == r2.modified_payload["content"] == "0123"


def test_deny_after_modify_keeps_accumulated_flags():
    """MODIFY 뒤 DENY가 와도 단락(short-circuit)하되, 그 전 MODIFY의 flags는 보존."""
    r = PolicyChain([_CapTo(8, 10), _Deny()]).evaluate(_a(), SharedState())
    assert r.verdict == Verdict.DENY and r.flags.get("cut_8") is True


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
