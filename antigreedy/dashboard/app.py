"""FastAPI A/B theater (T6 Phase B).

GET /   → the static two-panel theater (Cytoscape via CDN, no build step).
WS  /ws → triggers an A/B run and streams every event live; a final
          {"type": "done"} ends the stream.

The server is a thin event-log relay: it owns no view state, it just forwards
what run_ab emits (design §7 — the event log IS the product).
"""
from __future__ import annotations

import asyncio
import re
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

from antigreedy.backends import (
    LLMBackend, MockBackend, make_meeting_script, make_probe_script,
)
from antigreedy.dashboard.export import build_standalone_html
from antigreedy.dashboard.history import HistoryStore
from antigreedy.dashboard.live import make_live
from antigreedy.dashboard.runner import ABConfig, run_ab, run_probe
from antigreedy.events import EventStream
from antigreedy.scenario.meeting import MeetingConfig, run_meeting

REPO_POLICIES = Path(__file__).resolve().parent.parent.parent / "policies"
STATIC = Path(__file__).resolve().parent / "static"
DEFAULT_HISTORY = Path(__file__).resolve().parent.parent.parent / "runs" / "dashboard"

# Editor policy filenames: a bare name ending in .py, no path separators.
_FNAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.py")
_LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}


_AGENT_LETTERS = "ABCDEFGH"  # the meeting supports 2..8 agents


def _agents(n: int) -> list[str]:
    """Agent ids A.. for a meeting of N participants, clamped to [2, 8]."""
    n = max(2, min(len(_AGENT_LETTERS), int(n)))
    return list(_AGENT_LETTERS[:n])


def _clamp_budget(b: int) -> int:
    """Commons budget the UI may set, clamped to a sane [200, 8000] range."""
    return max(200, min(8000, int(b)))


def _is_local(host: str | None) -> bool:
    """True for loopback callers. The policy editor executes user-supplied
    Python server-side, so writes are gated to the presenter's own machine."""
    return host is None or host in _LOCAL_HOSTS


def _safe_filename(name: str) -> bool:
    return "/" not in name and ".." not in name and bool(_FNAME_RE.fullmatch(name))


def _list_policies(editor_dir: Path) -> list[dict[str, str]]:
    return [{"filename": p.name, "source": p.read_text(encoding="utf-8")}
            for p in sorted(editor_dir.glob("*.py"))]


# Named governance presets (PRD §4 "swap policy Y→Z live"). Each maps to a
# source dir of *.py policies; `None` = ungoverned. The default repo set
# (policies/*.py, top-level) is the "quota" preset; "strict" lives under
# policies/presets/strict. Applying one re-seeds the live editor dir.
def _preset_defs(policies_dir: Path) -> list[dict]:
    return [
        {"name": "none", "label": "None — ungoverned (baseline)", "dir": None},
        {"name": "quota", "label": "Airtime quota (default)", "dir": Path(policies_dir)},
        {"name": "strict", "label": "Strict quota (tighter cap)",
         "dir": Path(policies_dir) / "presets" / "strict"},
        # 사회심리학 기반 전략 (간접 상호성·가십·배제 / 보편화 / 조건부 협력)
        {"name": "social_reputation", "label": "사회: 평판·가십·배제 (Reputation+Ostracism)",
         "dir": Path(policies_dir) / "presets" / "social_reputation"},
        {"name": "social_universalization", "label": "사회: 보편화 (Universalization)",
         "dir": Path(policies_dir) / "presets" / "social_universalization"},
        {"name": "social_conditional", "label": "사회: 조건부 협력 (Conditional Cooperation)",
         "dir": Path(policies_dir) / "presets" / "social_conditional"},
        # 통합 스택: 배제 → 평판 캡 → 보편화 캡 (리서치 §2 Agent Society Governance Stack)
        {"name": "social_stack", "label": "사회: 통합 스택 (평판+배제+보편화)",
         "dir": Path(policies_dir) / "presets" / "social_stack"},
    ]


def _preset_files(d: Path | None) -> list[str]:
    return sorted(p.name for p in d.glob("*.py")) if d and d.exists() else []


def _apply_preset_files(editor_dir: Path, source_dir: Path | None) -> None:
    for old in editor_dir.glob("*.py"):
        old.unlink()
    if source_dir and source_dir.exists():
        for src in sorted(source_dir.glob("*.py")):
            shutil.copy2(src, editor_dir / src.name)


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
               real_backend_factory: Callable[[], LLMBackend] | None = None,
               cfg: ABConfig | None = None,
               editor_enabled: bool = True,
               localhost_only: bool = True,
               history_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Antigreedy A/B Theater")
    history = HistoryStore(history_dir or DEFAULT_HISTORY)
    baseline_dir = Path(tempfile.mkdtemp(prefix="ag_baseline_"))  # empty = ungoverned
    # Live editor dir: a writable COPY of the repo policy set. The governed arm
    # reads from here, so a policy pasted in the UI governs the next run without
    # touching the committed `policies/` dir.
    editor_dir = Path(tempfile.mkdtemp(prefix="ag_editor_"))
    for src in sorted(Path(policies_dir).glob("*.py")):
        shutil.copy2(src, editor_dir / src.name)
    governed_policies_dir = editor_dir
    html = (STATIC / "theater.html").read_text(encoding="utf-8")

    help_html = (STATIC / "help.html").read_text(encoding="utf-8")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return html

    @app.get("/help", response_class=HTMLResponse)
    async def help_page() -> str:
        return help_html

    @app.get("/config")
    async def config() -> dict:
        return {"real_available": real_backend_factory is not None}

    @app.get("/policies")
    async def list_policies() -> dict:
        return {"editable": editor_enabled, "localhost_only": localhost_only,
                "policies": _list_policies(editor_dir)}

    def _guard(request: Request) -> JSONResponse | None:
        if not editor_enabled:
            return JSONResponse({"error": "editor disabled"}, status_code=403)
        host = request.client.host if request.client else None
        if localhost_only and not _is_local(host):
            return JSONResponse({"error": "policy editor is localhost-only"},
                                status_code=403)
        return None

    @app.post("/policies")
    async def write_policy(request: Request) -> JSONResponse:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await request.json()
        filename = str(body.get("filename", ""))
        source = str(body.get("source", ""))
        if not _safe_filename(filename):
            return JSONResponse({"error": "filename must be a bare *.py name"},
                                status_code=400)
        try:
            compile(source, filename, "exec")  # reject syntax errors before writing
        except SyntaxError as exc:
            return JSONResponse({"error": f"syntax error: {exc.msg} (line {exc.lineno})"},
                                status_code=400)
        (editor_dir / filename).write_text(source, encoding="utf-8")
        return JSONResponse({"ok": True, "policies": _list_policies(editor_dir)})

    @app.delete("/policies/{filename}")
    async def delete_policy(filename: str, request: Request) -> JSONResponse:
        denied = _guard(request)
        if denied is not None:
            return denied
        if not _safe_filename(filename):
            return JSONResponse({"error": "bad filename"}, status_code=400)
        target = editor_dir / filename
        if target.exists():
            target.unlink()
        return JSONResponse({"ok": True, "policies": _list_policies(editor_dir)})

    @app.get("/presets")
    async def list_presets() -> dict:
        return {"presets": [{"name": p["name"], "label": p["label"],
                             "policies": _preset_files(p["dir"])}
                            for p in _preset_defs(policies_dir)]}

    @app.post("/presets/{name}/apply")
    async def apply_preset(name: str, request: Request) -> JSONResponse:
        denied = _guard(request)
        if denied is not None:
            return denied
        preset = next((p for p in _preset_defs(policies_dir) if p["name"] == name), None)
        if preset is None:
            return JSONResponse({"error": f"unknown preset '{name}'"}, status_code=404)
        _apply_preset_files(editor_dir, preset["dir"])
        return JSONResponse({"ok": True, "applied": name,
                             "policies": _list_policies(editor_dir)})

    @app.get("/history")
    async def history_list() -> dict:
        return {"runs": history.list()}

    @app.delete("/history")
    async def history_clear(request: Request) -> JSONResponse:
        denied = _guard(request)
        if denied is not None:
            return denied
        return JSONResponse({"ok": True, "cleared": history.clear()})

    @app.get("/history/{run_id}")
    async def history_get(run_id: str) -> JSONResponse:
        rec = history.get(run_id)
        if rec is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse(rec)

    @app.get("/history/{run_id}/export.html", response_class=HTMLResponse)
    async def history_export(run_id: str):
        rec = history.get(run_id)
        if rec is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        return HTMLResponse(build_standalone_html(rec))

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        # Optional first message: {"governed": bool}. The toggle button removes
        # governance by pointing the "governed" arm at the empty baseline policy
        # set, so both panels collapse — a live add/remove-governance demo.
        mode, governed = "ab", True
        run_cfg = cfg or ABConfig()
        use_real = False
        try:
            msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
            if isinstance(msg, dict):
                mode = msg.get("mode", "ab")
                governed = bool(msg.get("governed", True))
                # real LLM only when one is configured; otherwise fall back to mock
                use_real = msg.get("backend") == "real" and real_backend_factory is not None
                if msg.get("n_agents") is not None:  # configurable agent count
                    run_cfg = replace(run_cfg, agents=_agents(msg["n_agents"]))
                if msg.get("budget") is not None:    # configurable commons size
                    run_cfg = replace(run_cfg, budget=_clamp_budget(msg["budget"]))
                if isinstance(msg.get("personas"), dict):  # editable per-agent personas
                    run_cfg = replace(run_cfg, personas={
                        str(k): str(v)[:1000] for k, v in msg["personas"].items()})
        except asyncio.TimeoutError:
            pass
        except WebSocketDisconnect:
            return
        # pick the backend factory: real (if requested + available) else the mock defaults
        ab_factory = real_backend_factory if use_real else backend_factory
        probe_factory = real_backend_factory if use_real else probe_backend_factory
        live_factory = real_backend_factory if use_real else live_backend_factory
        queue: asyncio.Queue = asyncio.Queue()
        collected: list[dict] = []  # E3: accumulate the event log to persist the run

        def sink(ev: dict) -> None:
            collected.append(ev)
            queue.put_nowait(ev)

        def persist() -> None:
            try:
                history.save(mode=mode, events=collected)
            except OSError:
                pass  # history is best-effort; never break the live stream

        if mode == "live":
            await _run_live(websocket, queue, governed_policies_dir, baseline_dir,
                            live_factory(), run_cfg, sink=sink)
            persist()
            return
        if mode == "probe":
            task = asyncio.create_task(run_probe(
                governed_policies_dir, backend=probe_factory(),
                sink=sink, cfg=run_cfg))
        else:
            governed_dir = governed_policies_dir if governed else baseline_dir
            task = asyncio.create_task(run_ab(
                baseline_dir, governed_dir, backend=ab_factory(),
                sink=sink, cfg=run_cfg))
        try:
            while not (task.done() and queue.empty()):
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                await websocket.send_json(ev)
            await task  # surface any run error
            persist()
            await websocket.send_json({"type": "done"})
        except WebSocketDisconnect:
            task.cancel()

    return app


async def _run_live(websocket: WebSocket, queue: "asyncio.Queue",
                    policies_dir: Path, baseline_dir: Path,
                    backend: LLMBackend, cfg: ABConfig,
                    sink: Callable[[dict], None] | None = None) -> None:
    """Stream one paced meeting while concurrently accepting {"action": ...}
    control messages that flip governance ON/OFF live (one-touch apply/remove)."""
    lip, src, state = make_live(policies_dir, baseline_dir, backend,
                                max_tokens=cfg.live_max_tokens, delay=cfg.live_delay)
    stream = EventStream(cfg.run_id, "governed", 0, sink=sink or queue.put_nowait)
    mcfg = MeetingConfig(run_id=cfg.run_id, condition="governed", episode=0,
                         agents=list(cfg.agents),
                         personas={a: cfg.personas.get(a, "") for a in cfg.agents},
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
