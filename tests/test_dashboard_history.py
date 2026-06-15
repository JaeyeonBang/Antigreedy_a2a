"""E3 wiring: the dashboard persists each WS run and serves it back via
GET /history (list) and GET /history/{id} (full record for replay)."""
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import create_app
from antigreedy.dashboard.runner import ABConfig


def _app():
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=220, max_rounds=6),
        history_dir=Path(tempfile.mkdtemp(prefix="ag_hist_app_")))


def _run_ws(client, config=None):
    received = []
    with client.websocket_connect("/ws") as ws:
        if config is not None:
            ws.send_json(config)
        while True:
            ev = ws.receive_json()
            if ev.get("type") == "done":
                break
            received.append(ev)
    return received


def test_run_is_persisted_and_listed():
    client = TestClient(_app())
    assert client.get("/history").json()["runs"] == []  # empty before any run
    _run_ws(client, {"mode": "ab", "governed": True})
    runs = client.get("/history").json()["runs"]
    assert len(runs) == 1
    assert runs[0]["mode"] == "ab"
    assert "governed" in runs[0]["outcomes"]
    assert "events" not in runs[0]  # list view is lightweight


def test_get_history_record_returns_replayable_events():
    client = TestClient(_app())
    _run_ws(client, {"mode": "ab", "governed": True})
    run_id = client.get("/history").json()["runs"][0]["id"]
    rec = client.get(f"/history/{run_id}").json()
    assert any(e["type"] == "turn" for e in rec["events"])  # replayable event log
    assert client.get("/history/does-not-exist").status_code == 404


def test_index_has_history_ui():
    body = TestClient(_app()).get("/").text.lower()
    assert "history" in body
    assert 'id="hist-list"' in body or "id='hist-list'" in body
