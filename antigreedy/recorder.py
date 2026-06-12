"""Run recorder: JSONL event sink + LLM response cache (replay-ready, C-principle).

Cache key = sha256(model + prompt + temperature + seed) — recorded-run replay is
deterministic re-render; counterfactual replay is post-MVP (TODOS.md #1).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


class Recorder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def emit(self, event: dict[str, Any]) -> None:
        self._fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def read_events(path: str | Path) -> list[dict[str, Any]]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def cache_key(model: str, prompt: str, temperature: float, seed: int | None) -> str:
    h = hashlib.sha256()
    h.update(model.encode())
    h.update(prompt.encode())
    h.update(str(temperature).encode())
    h.update(str(seed).encode())
    return h.hexdigest()


class LLMCache:
    """File-backed prompt->response cache enabling free re-runs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: dict[str, dict] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text() or "{}")

    def get(self, key: str) -> dict | None:
        return self._data.get(key)

    def put(self, key: str, value: dict) -> None:
        self._data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False))
