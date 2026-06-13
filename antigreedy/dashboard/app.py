"""FastAPI A/B theater (T6 Phase B).

GET /   → the static two-panel theater (Cytoscape via CDN, no build step).
WS  /ws → triggers an A/B run and streams every event live; a final
          {"type": "done"} ends the stream.

The server is a thin event-log relay: it owns no view state, it just forwards
what run_ab emits (design §7 — the event log IS the product).
"""
from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from antigreedy.backends import (
    LLMBackend, MockBackend, make_meeting_script, make_probe_script,
)
from antigreedy.dashboard.runner import ABConfig, run_ab, run_probe

REPO_POLICIES = Path(__file__).resolve().parent.parent.parent / "policies"
STATIC = Path(__file__).resolve().parent / "static"


def _default_backend() -> LLMBackend:
    return MockBackend(make_meeting_script(dominator="A"))


def _default_probe_backend() -> LLMBackend:
    return MockBackend(make_probe_script())


def create_app(*, policies_dir: Path = REPO_POLICIES,
               backend_factory: Callable[[], LLMBackend] = _default_backend,
               probe_backend_factory: Callable[[], LLMBackend] = _default_probe_backend,
               cfg: ABConfig | None = None) -> FastAPI:
    app = FastAPI(title="Antigreedy A/B Theater")
    baseline_dir = Path(tempfile.mkdtemp(prefix="ag_baseline_"))  # empty = ungoverned
    html = (STATIC / "theater.html").read_text(encoding="utf-8")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return html

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        # Optional first message: {"governed": bool}. The toggle button removes
        # governance by pointing the "governed" arm at the empty baseline policy
        # set, so both panels collapse — a live add/remove-governance demo.
        mode, governed = "ab", True
        try:
            msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
            if isinstance(msg, dict):
                mode = msg.get("mode", "ab")
                governed = bool(msg.get("governed", True))
        except asyncio.TimeoutError:
            pass
        except WebSocketDisconnect:
            return
        queue: asyncio.Queue = asyncio.Queue()
        if mode == "probe":
            task = asyncio.create_task(run_probe(
                policies_dir, backend=probe_backend_factory(),
                sink=queue.put_nowait, cfg=cfg or ABConfig()))
        else:
            governed_dir = policies_dir if governed else baseline_dir
            task = asyncio.create_task(run_ab(
                baseline_dir, governed_dir, backend=backend_factory(),
                sink=queue.put_nowait, cfg=cfg or ABConfig()))
        try:
            while not (task.done() and queue.empty()):
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                await websocket.send_json(ev)
            await task  # surface any run error
            await websocket.send_json({"type": "done"})
        except WebSocketDisconnect:
            task.cancel()

    return app
