"""Standalone HTML export: a finished run can be exported as a single
self-contained HTML file that replays offline (no server, no WebSocket) — for
sharing a result or embedding in a slide deck."""
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import create_app
from antigreedy.dashboard.export import build_standalone_html
from antigreedy.dashboard.runner import ABConfig

RECORD = {
    "id": "20260616-000000-ab-1", "mode": "ab", "created_iso": "2026-06-16 00:00:00",
    "events": [
        {"type": "episode_start", "condition": "governed",
         "data": {"agents": ["A", "B"], "budget": 100}},
        {"type": "turn", "condition": "governed",
         "data": {"agent_id": "A", "round": 0, "verdict": "modify",
                  "attempted_tokens": 80, "delivered_tokens": 15, "commons_left": 85}},
        {"type": "episode_end", "condition": "governed",
         "data": {"outcome": "survived", "commons_left": 50,
                  "metrics": {"jain_delivered": 0.9, "delivered": {"A": 15, "B": 35},
                              "top_share": 0.7}}},
    ],
}


def test_build_standalone_html_is_self_contained():
    html = build_standalone_html(RECORD)
    assert html.startswith("<!DOCTYPE html>")
    assert RECORD["id"] in html                  # identifies the run
    assert "cytoscape" in html                    # graph renderer (CDN)
    assert "/ws" not in html                       # server-less: no WebSocket
    assert "episode_start" in html                 # the events are embedded


def test_export_endpoint_returns_html():
    app = create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=220, max_rounds=4),
        history_dir=Path(tempfile.mkdtemp(prefix="ag_exp_")))
    client = TestClient(app)
    # produce one run
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"mode": "ab", "governed": True})
        while ws.receive_json().get("type") != "done":
            pass
    run_id = client.get("/history").json()["runs"][0]["id"]
    r = client.get(f"/history/{run_id}/export.html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert run_id in r.text and r.text.startswith("<!DOCTYPE html>")
    assert client.get("/history/nope/export.html").status_code == 404
