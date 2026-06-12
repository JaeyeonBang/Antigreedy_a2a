from antigreedy.events import SCHEMA_VERSION, EventStream
from antigreedy.metrics import episode_summary, gate_report, jain, wilson_lower


def test_envelope_fields_and_seq():
    st = EventStream("r1", "governed", 3)
    e0 = st.emit("turn", {"agent_id": "A"}, policy_set_hash="abc")
    e1 = st.emit("decision", {})
    assert e0["schema_version"] == SCHEMA_VERSION
    assert (e0["run_id"], e0["condition"], e0["episode"]) == ("r1", "governed", 3)
    assert (e0["seq"], e1["seq"]) == (0, 1)
    assert e0["policy_set_hash"] == "abc" and "policy_set_hash" not in e1

def test_jain_known_vectors():
    assert abs(jain([1, 1, 1, 1]) - 1.0) < 1e-9
    assert abs(jain([1, 0, 0, 0]) - 0.25) < 1e-9
    assert jain([]) == 0.0 and jain([0, 0]) == 0.0

def test_wilson_known():
    assert wilson_lower(0, 0) == 0.0
    assert 0.39 < wilson_lower(7, 10) < 0.42      # 7/10 → ~0.397 (no power!)
    assert wilson_lower(18, 20) > 0.69            # 18/20 → strong

def _ep(events): return episode_summary(events)

def test_episode_summary_outcomes():
    st = EventStream("r", "baseline", 0)
    st.emit("turn", {"agent_id": "A", "round": 0, "attempted_tokens": 100,
                     "delivered_tokens": 60, "verdict": "modify"})
    st.emit("turn", {"agent_id": "B", "round": 0, "attempted_tokens": 30,
                     "delivered_tokens": 30, "verdict": "allow"})
    st.emit("episode_end", {"outcome": "exhausted", "commons_left": 0})
    s = _ep(st.events)
    assert s["outcome"] == "exhausted"
    assert s["attempted"] == {"A": 100, "B": 30}
    assert s["delivered"] == {"A": 60, "B": 30}
    assert s["jain_attempted"] != s["jain_delivered"]  # dual measurement is real

def test_gate_report_exclusions_and_verdict():
    def row(outcome, jd=0.5, ja=0.5):
        return {"outcome": outcome, "jain_delivered": jd, "jain_attempted": ja}
    baseline = [row("exhausted", jd=0.4)] * 9 + [row("cap_aborted")]
    governed = [row("decided", jd=0.9)] * 9 + [row("errored")]
    r = gate_report(baseline, governed)
    assert r["baseline_collapse"]["n"] == 9 and r["governed_flip"]["n"] == 9
    assert r["excluded"]["baseline"] == ["cap_aborted"]
    assert r["gate_passed"] is True
