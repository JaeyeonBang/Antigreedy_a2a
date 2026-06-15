"""Governance presets: pick a named, pre-set governance bundle (None / quota /
strict) from the dashboard and apply it to the governed side (PRD §4 "swap
policy Y→Z live"). Applying a preset re-seeds the live editor dir, so the next
governed run obeys the chosen set."""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import create_app
from antigreedy.dashboard.runner import ABConfig


def _app(**kw):
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=400, max_rounds=6), **kw)


def _gov_turns(events):
    return [e for e in events if e["type"] == "turn" and e["condition"] == "governed"]


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


def test_list_presets():
    body = TestClient(_app()).get("/presets").json()
    presets = {p["name"]: p for p in body["presets"]}
    assert {"none", "quota", "strict"} <= set(presets)
    assert presets["none"]["policies"] == []                       # ungoverned
    assert "10_airtime_quota.py" in presets["quota"]["policies"]   # the default set
    assert any("strict" in f for f in presets["strict"]["policies"])
    assert all(p.get("label") for p in body["presets"])            # human labels for the dropdown


def test_apply_none_makes_governed_ungoverned():
    client = TestClient(_app())
    r = client.post("/presets/none/apply")
    assert r.status_code == 200 and r.json()["applied"] == "none"
    assert client.get("/policies").json()["policies"] == []        # editor cleared
    gov = _gov_turns(_run_ws(client, {"governed": True}))
    assert gov and all(t["data"]["verdict"] == "allow" for t in gov)


def test_apply_strict_governs_harder():
    client = TestClient(_app())
    r = client.post("/presets/strict/apply")
    assert r.status_code == 200
    names = {p["filename"] for p in client.get("/policies").json()["policies"]}
    assert any("strict" in n for n in names)
    gov = _gov_turns(_run_ws(client, {"governed": True}))
    assert any(t["data"]["verdict"] in ("modify", "deny") for t in gov)  # governance bites


def test_apply_quota_restores_default():
    client = TestClient(_app())
    client.post("/presets/none/apply")
    client.post("/presets/quota/apply")
    names = {p["filename"] for p in client.get("/policies").json()["policies"]}
    assert "10_airtime_quota.py" in names


def test_apply_unknown_preset_404():
    assert TestClient(_app()).post("/presets/bogus/apply").status_code == 404


def test_apply_gated_when_editor_disabled():
    assert TestClient(_app(editor_enabled=False)).post("/presets/strict/apply").status_code == 403


def test_index_has_preset_selector():
    body = TestClient(_app()).get("/").text.lower()
    assert 'id="preset"' in body or "id='preset'" in body
    assert "preset" in body
