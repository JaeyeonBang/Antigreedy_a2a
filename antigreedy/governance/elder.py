"""Elder 원장 + 평판 혼합 (Phase 2, design D-Elder + E-세탁/카스트갭).

설계 질문: rule(행동) 평판에 LLM-judge를 섞은 ``rep = α·rule + (1−α)·llm``이 rule-only보다
*진짜 신호*를 더하나(아니면 또 앵커링인가, V6 교훈)? 그리고 *불변 원장*이 LLM 오판을 영구화해
카스트를 만드나? 평판 *세탁*(잠깐 착해져 평판 리셋)에 견디나?

구성:
- ``ElderLedger``: append-only 원장(불변). 한 번 적힌 심사는 수정/삭제되지 않는다(=불변성의 위험을
  실험으로 노출). ``state.extra["elder_ledger"]``에 보관, 기록자는 ``ElderInterceptPoint`` 하나뿐.
- ``elder_reputation(rule_rep, llm_scores, alpha)``: 두 신호의 α-가중 혼합(순수함수).
- ``ElderInterceptPoint``: InterceptPoint. 에이전트별 *최초 1회* judge(검소) → 점수 캐시 + 원장 기록,
  이후 매 턴 rule 평판(Beta+λ)과 혼합해 배제+캡. judge_fn=None이면 LLM 없이 numeric 앵커(대조군).
"""
from __future__ import annotations

from antigreedy.governance.types import (
    AgentAction, PolicyResult, SharedState, Verdict,
)
from antigreedy.governance.reputation_calc import beta_reputation, share_of, _n_agents
from antigreedy.governance.elder_judge import numeric_judge

BASE_SHARE = 0.22
CHARS_PER_TOKEN = 4


class ElderLedger:
    """불변(append-only) 평판 원장. 심사는 추가만 — 한 번 적히면 못 지운다(카스트 위험의 근원)."""

    def __init__(self) -> None:
        self.entries: list[dict] = []

    def record(self, judge: str, target: str, score: float, round: int) -> None:
        self.entries.append({"judge": judge, "target": target,
                             "score": float(score), "round": int(round)})

    def scores_for(self, target: str) -> list[float]:
        return [e["score"] for e in self.entries if e["target"] == target]


def elder_reputation(rule_rep: float, llm_scores: list[float], alpha: float) -> float:
    """rep = α·rule + (1−α)·mean(llm). 심사 점수가 없으면 rule만(앵커링 회피). α=1 → rule-only."""
    if not llm_scores:
        return rule_rep
    llm = sum(llm_scores) / len(llm_scores)
    return alpha * rule_rep + (1.0 - alpha) * llm


class ElderInterceptPoint:
    """Elder 평판으로 구동되는 배제+캡 InterceptPoint (judge 1회/에이전트, 검소).

    ``judge_fn``: ``async (agent, justification, share, fair) -> float`` 또는 None(=numeric 앵커).
    ``alpha``: rule 가중(1.0이면 judge 미호출 = 순수 rule arm). ``lam``/``lam_down``: rule Beta 망각.
    """

    def __init__(self, state: SharedState, alpha: float = 0.5, judge_fn=None,
                 lam: float = 1.0, lam_down: float | None = None,
                 thresh: float = 0.45, floor: int = 30) -> None:
        self._state = state
        self.alpha = alpha
        self._judge_fn = judge_fn
        self.lam = lam
        self.lam_down = lam_down
        self.thresh = thresh
        self.floor = floor
        self._history: list = []

    async def submit(self, action: AgentAction) -> PolicyResult:
        state = self._state
        agent = action.agent_id
        ledger: ElderLedger = state.extra.setdefault("elder_ledger", ElderLedger())
        scores: dict = state.extra.setdefault("elder_scores", {})
        # 에이전트별 최초 1회 심사 (α=1 순수 rule arm은 심사 자체를 생략 → 비용 0)
        if (action.action_type == "message" and self.alpha < 1.0 and agent not in scores):
            share = share_of(agent, state)
            fair = 1.0 / _n_agents(state)
            if self._judge_fn is not None:
                sc = await self._judge_fn(agent, action.payload.get("justification", ""), share, fair)
                tag = "elder"
            else:
                sc = numeric_judge(share, fair)
                tag = "numbers"
            scores[agent] = sc
            ledger.record(judge=tag, target=agent, score=sc, round=action.round)
        res = self._decide(action, state, scores)
        self._history.append((action, res))
        return res

    def _decide(self, action: AgentAction, state: SharedState, scores: dict) -> PolicyResult:
        name = self.policy_set_hash()
        if action.action_type != "message":
            return PolicyResult(Verdict.ALLOW, reason="not a message", policy_name=name)
        if not state.turn_log:
            return PolicyResult(Verdict.ALLOW, reason="평판 근거 없음", policy_name=name)
        agent = action.agent_id
        rule_rep, share = beta_reputation(agent, state, self.lam, self.lam_down)
        llm_scores = [scores[agent]] if agent in scores else []
        erep = elder_reputation(rule_rep, llm_scores, self.alpha)
        if erep < self.thresh:
            return PolicyResult(Verdict.DENY, policy_name=name,
                                reason=f"배제(elder α={self.alpha}) — 평판 {erep:.2f}<{self.thresh}",
                                flags={"ostracized": True, "airtime_greedy": True})
        remaining = state.commons.get("token_budget_remaining")
        if remaining is None or action.token_estimate <= 0:
            return PolicyResult(Verdict.ALLOW, reason="no commons tracked", policy_name=name)
        cap = max(self.floor, int(remaining * BASE_SHARE * erep))
        if action.token_estimate <= cap:
            return PolicyResult(Verdict.ALLOW, policy_name=name,
                                reason=f"평판 {erep:.2f} 양호 (점유 {share:.2f})")
        content = action.payload.get("content", "")
        return PolicyResult(Verdict.MODIFY, policy_name=name,
                            modified_payload={**action.payload,
                                              "content": content[: cap * CHARS_PER_TOKEN],
                                              "_truncated": True},
                            reason=f"평판 {erep:.2f} → {action.token_estimate}>{cap} 축약",
                            flags={"airtime_greedy": True})

    def policy_set_hash(self) -> str:
        kind = "rule" if self.alpha >= 1.0 else ("elder" if self._judge_fn is not None else "numbers")
        return f"elder:{kind}:alpha={self.alpha}"
