"""T6 Phase B: the FastAPI dashboard. A WebSocket connection triggers an A/B run
and streams every event live; a final {"type": "done"} closes the stream. The
index route serves the static A/B theater HTML.
"""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import create_app
from antigreedy.dashboard.runner import ABConfig


def _app():
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=220, max_rounds=6))


def test_ws_streams_both_conditions_then_done():
    client = TestClient(_app())
    received = []
    with client.websocket_connect("/ws") as ws:
        while True:
            ev = ws.receive_json()
            if ev.get("type") == "done":
                break
            received.append(ev)
    assert {e["condition"] for e in received} == {"baseline", "governed"}
    assert sum(1 for e in received if e["type"] == "episode_end") == 2
    assert any(e["type"] == "turn" for e in received)


def test_main_entry_wires_uvicorn(monkeypatch):
    import antigreedy.dashboard.__main__ as m
    calls = {}
    monkeypatch.setattr(m.uvicorn, "run",
                        lambda app, **kw: calls.update(kw, app=app))
    monkeypatch.setattr("sys.argv", ["antigreedy.dashboard", "--port", "9999"])
    m.main()
    assert calls["port"] == 9999 and calls["app"] is not None


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


def _gov_turns(events):
    return [e for e in events if e["type"] == "turn" and e["condition"] == "governed"]


def test_governance_toggle_off_removes_truncation():
    client = TestClient(_app())
    # toggle OFF → the governed panel runs WITHOUT policies → no modify/deny verdicts
    off = _gov_turns(_run_ws(client, {"governed": False}))
    assert off and all(t["data"]["verdict"] == "allow" for t in off)


def test_governance_toggle_on_truncates():
    client = TestClient(_app())
    on = _gov_turns(_run_ws(client, {"governed": True}))
    assert any(t["data"]["verdict"] == "modify" for t in on)  # governance applied


def test_index_serves_html():
    client = TestClient(_app())
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    body = r.text.lower()
    assert "baseline" in body and "governed" in body  # the two panels (ids/classes)
    assert "거버넌스" in body  # the toggle control (Korean UI)


def test_ws_resource_scenario_streams_completion():
    client = TestClient(_app())
    received = _run_ws(client, {"mode": "ab", "governed": True, "scenario": "resource",
                                "n_agents": 4})
    ends = [e for e in received if e["type"] == "episode_end"]
    assert ends and {e["condition"] for e in ends} == {"baseline", "governed"}
    # resource scenario reports task completion (welfare), not just airtime
    gov = next(e for e in ends if e["condition"] == "governed")
    assert "completion_rate" in gov["data"]["metrics"]
    assert "starved" in gov["data"]["metrics"]


def test_help_page_serves_definitions():
    r = TestClient(_app()).get("/help")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    body = r.text
    assert "도움말" in body
    assert "커먼즈" in body and "기만" in body          # commons + deception
    assert "top_share" in body and "Jain" in body       # formal metrics
    assert "deceptive(true, reported, tol)" in body      # deception formula
    # the dashboard links to it
    assert "/help" in TestClient(_app()).get("/").text


def test_index_is_beginner_friendly():
    """E1: a first-time viewer can use every feature without docs — jargon
    glosses, a legend, empty-state guidance, and per-button explanations.
    The dashboard copy is Korean."""
    body = TestClient(_app()).get("/").text.lower()
    # jargon glosses (Korean)
    assert "공유 토큰 예산" in body                 # commons explained
    assert "발언량" in body                         # airtime explained
    # legend mapping the visuals (node colour = verdict, size = airtime)
    assert "범례" in body
    assert "allow" in body and "modify" in body and "deny" in body  # verdict tokens kept
    # empty-state guidance before any run
    assert "시작" in body
    # per-button help text (beyond the bare button labels)
    assert "나란히" in body or "하는 일" in body
