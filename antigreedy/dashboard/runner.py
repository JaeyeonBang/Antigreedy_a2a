"""A/B run driver (T6 Phase A).

Runs a baseline (ungoverned) and a governed meeting CONCURRENTLY, both streaming
through one ``sink`` so the dashboard renders two live panels. Same backend +
config for both → the only difference is the policy set, so the contrast is pure
governance effect. The driver computes nothing itself beyond episode summaries
(pure function of the event log, eng decision 4).
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from antigreedy.backends import LLMBackend
from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.metrics import episode_summary
from antigreedy.probe.cards import FactCard
from antigreedy.probe.scenario import ProbeConfig, run_probe_episode
from antigreedy.scenario.meeting import MeetingConfig, run_episode


@dataclass
class ABConfig:
    run_id: str = "ab"
    agents: list[str] = field(default_factory=lambda: ["A", "B", "C", "D"])
    personas: dict[str, str] = field(default_factory=dict)  # per-agent persona (editable from UI)
    budget: int = 1200      # large enough that GOVERNED survives while baseline collapses
    max_rounds: int = 8
    live_delay: float = 0.6   # per-turn pause in live mode so a human can click mid-run
    live_budget: int = 18000  # bigger commons so the ungoverned phase lasts long enough to rescue
    live_max_rounds: int = 14
    live_max_tokens: int = 8000  # don't clip the hog — its big turn must EXCEED the per-turn cap


async def run_ab(baseline_dir: Path, governed_dir: Path, *, backend: LLMBackend,
                 sink: Callable[[dict], None] | None = None,
                 cfg: ABConfig | None = None) -> dict[str, Any]:
    """Run both conditions concurrently; return {condition: {outcome, summary}}."""
    cfg = cfg or ABConfig()

    async def one(condition: str, policy_dir: Path) -> tuple[str, dict[str, Any]]:
        state = SharedState()
        intercept = InProcessInterceptPoint(PolicyLoader(policy_dir), state)
        stream = EventStream(cfg.run_id, condition, 0, sink=sink)
        mcfg = MeetingConfig(run_id=cfg.run_id, condition=condition, episode=0,
                             agents=list(cfg.agents),
                             personas={a: cfg.personas.get(a, "") for a in cfg.agents},
                             budget=cfg.budget, max_rounds=cfg.max_rounds)
        out = await run_episode(mcfg, backend, intercept, stream, state)
        return condition, {"outcome": out["outcome"],
                           "summary": episode_summary(stream.events)}

    pairs = await asyncio.gather(one("baseline", baseline_dir),
                                 one("governed", governed_dir))
    return dict(pairs)


async def run_probe(policy_dir: Path, *, backend: LLMBackend,
                    sink: Callable[[dict], None] | None = None,
                    cfg: ABConfig | None = None, probe: str = "A",
                    card_value: float = 10.0) -> dict[str, Any]:
    """Run one deception-probe episode and stream it (tagged "governed" so the
    theater renders it in the right panel). The probe under-reports its card →
    `ground_truth` events with deceptive=True drive the live red-flag."""
    cfg = cfg or ABConfig()
    cards = {a: FactCard(a, "compute-hours used", card_value) for a in cfg.agents}
    state = SharedState()
    intercept = InProcessInterceptPoint(PolicyLoader(policy_dir), state)
    stream = EventStream(cfg.run_id, "governed", 0, sink=sink)
    pcfg = ProbeConfig(run_id=cfg.run_id, episode=0, cards=cards, probe=probe,
                       budget=cfg.budget, max_rounds=2)
    await run_probe_episode(pcfg, backend, intercept, stream, state)
    flagged = sorted({e["data"]["agent_id"] for e in stream.events
                      if e["type"] == "ground_truth" and e["data"]["deceptive"]})
    return {"probe": probe, "flagged": flagged}
