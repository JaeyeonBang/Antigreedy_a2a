"""T6 probe red-flag: a deterministic deception probe wired into the dashboard.
The probe agent under-reports its private card → objective `ground_truth`
events mark it deceptive → the theater lights it up red live.
"""
import asyncio

from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_probe_script
from antigreedy.dashboard.app import create_app
from antigreedy.dashboard.runner import ABConfig, run_probe
from antigreedy.probe.cards import FactCard
from antigreedy.probe.scenario import build_probe_prompt
from antigreedy.protocol import parse_turn


def test_probe_script_under_reports_only_the_probe():
    card = FactCard("A", "compute-hours", 10.0)
    script = make_probe_script(under_report_factor=0.5)
    probe_turn = parse_turn(script(build_probe_prompt("A", "t", card, True, "", 0, 4000)))
    honest_turn = parse_turn(script(build_probe_prompt("B", "t", card, False, "", 0, 4000)))
    assert probe_turn.report == 5.0    # under-reported (10 * 0.5)
    assert honest_turn.report == 10.0  # truthful


def test_run_probe_flags_the_deceiver(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    events = []
    res = asyncio.run(run_probe(d, backend=MockBackend(make_probe_script()),
                                sink=events.append,
                                cfg=ABConfig(run_id="t"), probe="A"))
    gt = [e for e in events if e["type"] == "ground_truth"]
    assert gt, "ground_truth events must stream"
    assert any(e["data"]["deceptive"] for e in gt if e["data"]["agent_id"] == "A")
    assert res["flagged"] == ["A"]          # only the probe is caught
    assert all(e["condition"] == "governed" for e in events)  # right-panel tagged


def test_ws_probe_mode_streams_ground_truth():
    app = create_app(
        probe_backend_factory=lambda: MockBackend(make_probe_script()),
        cfg=ABConfig(run_id="t", budget=4000))
    client = TestClient(app)
    received = []
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"mode": "probe"})
        while True:
            ev = ws.receive_json()
            if ev.get("type") == "done":
                break
            received.append(ev)
    gt = [e for e in received if e["type"] == "ground_truth"]
    assert any(e["data"]["deceptive"] and e["data"]["is_probe"] for e in gt)
