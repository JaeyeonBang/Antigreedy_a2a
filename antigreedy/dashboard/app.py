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
from antigreedy.dashboard.live import make_live
from antigreedy.dashboard.runner import ABConfig, run_ab, run_probe
from antigreedy.events import EventStream
from antigreedy.scenario.meeting import MeetingConfig, run_meeting

REPO_POLICIES = Path(__file__).resolve().parent.parent.parent / "policies"
STATIC = Path(__file__).resolve().parent / "static"


def _default_backend() -> LLMBackend:
    return MockBackend(make_meeting_script(dominator="A"))


def _default_probe_backend() -> LLMBackend:
    return MockBackend(make_probe_script())


def _default_live_backend() -> LLMBackend:
    # a genuinely greedy hog: big per-turn so governance truncates it the instant it's applied
    return MockBackend(make_meeting_script(dominator="A", verbose_words=2500))


def create_app(*, policies_dir: Path = REPO_POLICIES,
               backend_factory: Callable[[], LLMBackend] = _default_backend,
               probe_backend_factory: Callable[[], LLMBackend] = _default_probe_backend,
               live_backend_factory: Callable[[], LLMBackend] = _default_live_backend,
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
        if mode == "live":
            await _run_live(websocket, queue, policies_dir, baseline_dir,
                            live_backend_factory(), cfg or ABConfig())
            return
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


async def _run_live(websocket: WebSocket, queue: "asyncio.Queue",
                    policies_dir: Path, baseline_dir: Path,
                    backend: LLMBackend, cfg: ABConfig) -> None:
    """Stream one paced meeting while concurrently accepting {"action": ...}
    control messages that flip governance ON/OFF live (one-touch apply/remove)."""
    lip, src, state = make_live(policies_dir, baseline_dir, backend,
                                max_tokens=cfg.live_max_tokens, delay=cfg.live_delay)
    stream = EventStream(cfg.run_id, "governed", 0, sink=queue.put_nowait)
    mcfg = MeetingConfig(run_id=cfg.run_id, condition="governed", episode=0,
                         agents=list(cfg.agents),
                         personas={a: "" for a in cfg.agents},
                         budget=cfg.live_budget, max_rounds=cfg.live_max_rounds)
    meeting = asyncio.create_task(run_meeting(mcfg, src, stream, state))

    async def control() -> None:
        while not meeting.done():
            try:
                m = await asyncio.wait_for(websocket.receive_json(), timeout=0.15)
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                meeting.cancel()
                return
            if isinstance(m, dict) and "action" in m:
                lip.governance_on = (m["action"] == "govern_on")

    ctl = asyncio.create_task(control())
    try:
        while not (meeting.done() and queue.empty()):
            try:
                ev = await asyncio.wait_for(queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            await websocket.send_json(ev)
        await meeting
        await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        meeting.cancel()
    finally:
        ctl.cancel()
