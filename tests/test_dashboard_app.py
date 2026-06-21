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


def test_ws_resource_applies_shapers_to_governed_prompts_only():
    """행동(입력)측 거버넌스: WS `shapers` 파라미터가 governed arm의 프롬프트만 재구성하고
    baseline은 손대지 않는다(순수 대조). 평판 되먹임 cue가 governed 프롬프트에 주입됨."""
    client = TestClient(_app())
    received = _run_ws(client, {"mode": "ab", "governed": True, "scenario": "resource",
                                "n_agents": 3, "shapers": ["reputation_feedback"]})
    turns = [e for e in received if e["type"] == "turn"]
    gov = [t for t in turns if t["condition"] == "governed"]
    base = [t for t in turns if t["condition"] == "baseline"]
    assert gov and any("REPUTATION FEEDBACK" in t["data"]["prompt"] for t in gov)
    assert base and all("REPUTATION FEEDBACK" not in t["data"]["prompt"] for t in base)


def test_ws_unknown_shaper_is_filtered_out():
    """모르는 shaper 이름은 무시(견고성) — 크래시 없이 정상 스트림 완료."""
    client = TestClient(_app())
    received = _run_ws(client, {"mode": "ab", "governed": True, "scenario": "resource",
                                "n_agents": 3, "shapers": ["nope", "reputation_feedback"]})
    assert any(e["type"] == "episode_end" for e in received)


def test_index_exposes_behavioral_governance_control():
    """대시보드가 행동측 거버넌스(shaper) 선택 UI를 노출한다."""
    body = TestClient(_app()).get("/").text
    assert "행동" in body and ("평판 되먹임" in body or "reputation_feedback" in body)


def test_governance_doc_serves_strategies_and_results():
    r = TestClient(_app()).get("/governance")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    body = r.text
    # documents each governance proposal from research_2.md §5.2
    for term in ["간접 상호성", "배제", "상위 정체성", "책임성", "보편화", "조건부 협력", "통합 스택"]:
        assert term in body, f"missing governance: {term}"
    # experiment design + measured results present
    assert "실험 설계" in body and "실험 결과" in body
    assert "top_share" in body and "완료율" in body
    assert "cap-null" in body or "cap-null ablation" in body
    # the dashboard links to it
    assert "/governance" in TestClient(_app()).get("/").text


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
