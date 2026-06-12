import textwrap
from pathlib import Path
from antigreedy.governance import AgentAction, SharedState, Verdict
from antigreedy.governance.loader import PolicyLoader

V1 = """
from antigreedy.governance.policy import Policy
class Cap(Policy):
    name, priority, LIMIT = "cap", 10, 100
    def evaluate(self, a, s, h):
        return self.allow() if a.token_estimate <= self.LIMIT else self.deny(reason=f">{self.LIMIT}")
"""
V2 = V1.replace("100", "10")

def _w(p, t): p.write_text(textwrap.dedent(t).lstrip())

def test_edit_changes_verdict_without_restart(tmp_path):
    d = tmp_path / "pol"; d.mkdir(); f = d / "cap.py"; _w(f, V1)
    L = PolicyLoader(d); a = AgentAction(agent_id="x", token_estimate=50)
    assert L.chain.evaluate(a, SharedState()).verdict == Verdict.ALLOW
    _w(f, V2); L.load_file(f)
    assert L.chain.evaluate(a, SharedState()).verdict == Verdict.DENY

def test_add_remove(tmp_path):
    d = tmp_path / "pol"; d.mkdir(); L = PolicyLoader(d)
    assert L.policy_names() == []
    f = d / "b.py"
    _w(f, """
from antigreedy.governance.policy import Policy
class B(Policy):
    name, priority = "blocker", 5
    def evaluate(self, a, s, h): return self.deny(reason="b")
""")
    L.load_file(f)
    assert "blocker" in L.policy_names()
    f.unlink(); L.reload_all()
    assert L.policy_names() == []

def test_freeze_ignores_reload(tmp_path):
    d = tmp_path / "pol"; d.mkdir(); f = d / "cap.py"; _w(f, V1)
    L = PolicyLoader(d); h1 = L.policy_set_hash()
    L.freeze(); _w(f, V2); L.load_file(f)
    a = AgentAction(agent_id="x", token_estimate=50)
    assert L.chain.evaluate(a, SharedState()).verdict == Verdict.ALLOW  # still V1
    assert L.policy_set_hash() == h1
    L.thaw(); L.load_file(f)
    assert L.chain.evaluate(a, SharedState()).verdict == Verdict.DENY
    assert L.policy_set_hash() != h1

def test_syntax_error_keeps_previous(tmp_path):
    d = tmp_path / "pol"; d.mkdir(); f = d / "cap.py"; _w(f, V1)
    L = PolicyLoader(d)
    f.write_text("def broken(:\n")
    L.load_file(f)
    assert "cap" in L.policy_names()  # previous version retained

def test_repo_policies_dir_loads():
    L = PolicyLoader(Path(__file__).resolve().parent.parent / "policies")
    assert {"airtime_quota", "allow_all"} <= set(L.policy_names())
