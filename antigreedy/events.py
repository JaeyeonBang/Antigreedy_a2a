"""Replay-ready event envelope (eng decisions 2, 13, outside #8).

Every event carries {run_id, condition, episode, seq, schema_version}; verdict
events additionally carry policy_set_hash. Metrics are a pure function of these
events (eng decision 4) — never of live state.
"""
from __future__ import annotations
import time
from typing import Any

SCHEMA_VERSION = 1


class EventStream:
    """Per-episode event factory + buffer; seq is monotonically increasing."""

    def __init__(self, run_id: str, condition: str, episode: int,
                 sink=None) -> None:
        self.run_id = run_id
        self.condition = condition  # "baseline" | "governed" | "emergent" ...
        self.episode = episode
        self._seq = 0
        self._sink = sink  # optional callable(event_dict), e.g. Recorder.emit
        self.events: list[dict[str, Any]] = []

    def emit(self, type_: str, data: dict[str, Any],
             policy_set_hash: str | None = None) -> dict[str, Any]:
        ev: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "condition": self.condition,
            "episode": self.episode,
            "seq": self._seq,
            "ts": time.time(),
            "type": type_,
            "data": data,
        }
        if policy_set_hash is not None:
            ev["policy_set_hash"] = policy_set_hash
        self._seq += 1
        self.events.append(ev)
        if self._sink is not None:
            self._sink(ev)
        return ev
