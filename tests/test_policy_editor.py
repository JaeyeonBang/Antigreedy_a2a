"""E2: in-dashboard policy editor. The user pastes a Policy subclass in the UI →
the server writes it into a live (non-frozen) policy dir → the next governed run
picks it up. Executes user Python server-side, so it is gated localhost-only with
a clear warning (presenter's own machine; never exposed publicly).
"""
from fastapi.testclient import TestClient

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.app import _is_local, create_app
from antigreedy.dashboard.runner import ABConfig

DENY_A = '''
from antigreedy.governance.policy import Policy

class DenyA(Policy):
    name = "deny_a"
    priority = 1
    def evaluate(self, action, state, history):
        if action.agent_id == "A":
            return self.deny(reason="A muted by pasted policy")
        return self.allow()
'''


def _app(**kw):
    return create_app(
        backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        cfg=ABConfig(run_id="t", budget=220, max_rounds=6), **kw)


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


# ---- listing -------------------------------------------------------------
def test_list_policies_returns_seeded_set():
    r = TestClient(_app()).get("/policies")
    assert r.status_code == 200
    body = r.json()
    assert body["editable"] is True
    names = {p["filename"] for p in body["policies"]}
    assert "10_airtime_quota.py" in names  # seeded from the repo policy dir
    quota = next(p for p in body["policies"] if p["filename"] == "10_airtime_quota.py")
    assert "class" in quota["source"]  # full source is returned for editing


# ---- write + govern (the live "wow") -------------------------------------
def test_post_policy_then_governed_run_applies_it():
    client = TestClient(_app())
    r = client.post("/policies", json={"filename": "99_deny_a.py", "source": DENY_A})
    assert r.status_code == 200 and r.json()["ok"] is True
    assert "99_deny_a.py" in {p["filename"] for p in client.get("/policies").json()["policies"]}
    # the pasted policy now governs the next run: A's turns are denied
    gov = _gov_turns(_run_ws(client, {"governed": True}))
    assert any(t["data"]["agent_id"] == "A" and t["data"]["verdict"] == "deny" for t in gov)


def test_delete_policy_removes_it():
    client = TestClient(_app())
    client.post("/policies", json={"filename": "99_deny_a.py", "source": DENY_A})
    r = client.delete("/policies/99_deny_a.py")
    assert r.status_code == 200
    assert "99_deny_a.py" not in {p["filename"] for p in r.json()["policies"]}


# ---- validation / security ----------------------------------------------
def test_post_rejects_path_traversal_filename():
    client = TestClient(_app())
    r = client.post("/policies", json={"filename": "../evil.py", "source": "x=1"})
    assert r.status_code == 400


def test_post_rejects_non_python_filename():
    client = TestClient(_app())
    r = client.post("/policies", json={"filename": "evil.sh", "source": "x=1"})
    assert r.status_code == 400


def test_post_rejects_syntax_error():
    client = TestClient(_app())
    r = client.post("/policies", json={"filename": "90_broken.py", "source": "def ("})
    assert r.status_code == 400
    assert "error" in r.json()


def test_editor_disabled_returns_403():
    client = TestClient(_app(editor_enabled=False))
    assert client.get("/policies").json()["editable"] is False
    r = client.post("/policies", json={"filename": "99_deny_a.py", "source": DENY_A})
    assert r.status_code == 403


def test_index_has_editor_ui_with_warning():
    """The dashboard ships the editor UI inline, with the localhost-only warning
    so a presenter understands it runs their pasted Python on their machine."""
    body = TestClient(_app()).get("/").text.lower()
    assert "policy editor" in body
    assert "localhost" in body            # the security warning
    assert "id=\"pol-source\"" in body or "id='pol-source'" in body   # the textarea
    assert "save policy" in body or "save &amp; apply" in body or "save policy" in body


def test_is_local_gate():
    assert _is_local("127.0.0.1") and _is_local("::1") and _is_local("testclient")
    assert _is_local("localhost") and _is_local(None)
    assert not _is_local("8.8.8.8") and not _is_local("10.0.0.5")
