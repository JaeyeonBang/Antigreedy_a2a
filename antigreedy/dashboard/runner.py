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
from antigreedy.scenario.meeting import MeetingConfig, run_episode


@dataclass
class ABConfig:
    run_id: str = "ab"
    agents: list[str] = field(default_factory=lambda: ["A", "B", "C", "D"])
    budget: int = 400
    max_rounds: int = 6


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
                             personas={a: "" for a in cfg.agents},
                             budget=cfg.budget, max_rounds=cfg.max_rounds)
        out = await run_episode(mcfg, backend, intercept, stream, state)
        return condition, {"outcome": out["outcome"],
                           "summary": episode_summary(stream.events)}

    pairs = await asyncio.gather(one("baseline", baseline_dir),
                                 one("governed", governed_dir))
    return dict(pairs)
