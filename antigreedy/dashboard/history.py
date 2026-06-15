"""Experiment history (T6 / PRD §12 E3).

Persists every dashboard run — its mode, derived outcomes, and the FULL event
log — as one JSON file per run under a directory (default ``runs/``, gitignored).
The event log is the product (design §7), so a run is replayable: the dashboard
re-feeds the stored events through the same ``handle`` renderer to re-open it.

Records are pure functions of the event log (eng decision 4): outcomes and the
policy-set hash are derived here, never tracked as live state.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_COUNTER = {"n": 0}


def _derive(mode: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = {e["condition"]: e["data"].get("outcome")
                for e in events if e.get("type") == "episode_end" and e.get("condition")}
    fairness = {e["condition"]: e["data"]["metrics"].get("jain_delivered")
                for e in events if e.get("type") == "episode_end" and e.get("condition")
                and isinstance(e["data"].get("metrics"), dict)}
    psh = next((e["policy_set_hash"] for e in events if e.get("policy_set_hash")), "")
    n_turns = sum(1 for e in events if e.get("type") == "turn")
    deceptions = sorted({e["data"].get("agent_id") for e in events
                         if e.get("type") == "ground_truth" and e["data"].get("deceptive")})
    return {"mode": mode, "outcomes": outcomes, "fairness": fairness, "policy_set_hash": psh,
            "n_turns": n_turns, "n_events": len(events), "deceptions": deceptions}


class HistoryStore:
    def __init__(self, directory: str | Path) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, *, mode: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Persist a run; return its lightweight summary (no events)."""
        now = time.time()
        _COUNTER["n"] += 1
        run_id = f"{time.strftime('%Y%m%d-%H%M%S', time.localtime(now))}-{mode}-{_COUNTER['n']}"
        summary = {"id": run_id, "created_at": now,
                   "created_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
                   **_derive(mode, events)}
        record = {**summary, "events": events}
        (self.dir / f"{run_id}.json").write_text(
            json.dumps(record, ensure_ascii=False), encoding="utf-8")
        return summary

    def list(self) -> list[dict[str, Any]]:
        """All run summaries (events omitted), newest first."""
        out = []
        for path in self.dir.glob("*.json"):
            try:
                rec = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            rec.pop("events", None)
            out.append(rec)
        return sorted(out, key=lambda r: r.get("created_at", 0), reverse=True)

    def clear(self) -> int:
        """Delete all persisted runs; return how many were removed."""
        n = 0
        for path in self.dir.glob("*.json"):
            try:
                path.unlink()
                n += 1
            except OSError:
                pass
        return n

    def get(self, run_id: str) -> dict[str, Any] | None:
        """Full record (with events) for one run, or None if unknown."""
        path = self.dir / f"{run_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
