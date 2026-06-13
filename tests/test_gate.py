import asyncio
from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.gate import run_condition, run_gate
from antigreedy.metrics import gate_report


def _ep(outcome, jain_delivered, jain_attempted=0.72):
    return {"outcome": outcome, "jain_delivered": jain_delivered,
            "jain_attempted": jain_attempted, "attempted": {}, "delivered": {}}


def test_gate_passes_on_relative_fairness_effect():
    # mirrors the live 10v10: baseline reliably exhausts (jain ~0.625),
    # governed reliably survives and is far fairer (jain ~0.908)
    baseline = [_ep("exhausted", 0.625)] * 9 + [_ep("decided", 0.625)]
    governed = [_ep("survived", 0.908)] * 10
    rep = gate_report(baseline, governed)
    assert rep["collapse_confirmed"] and rep["flip_confirmed"]
    assert rep["fairness_confirmed"] and rep["gate_passed"]
    assert rep["fairness_gain"] > 0.15


def test_gate_fails_without_a_real_fairness_gain():
    # both arms already fair → governance adds little → must NOT pass
    baseline = [_ep("exhausted", 0.80)] * 10
    governed = [_ep("survived", 0.85)] * 10
    rep = gate_report(baseline, governed)
    assert not rep["fairness_confirmed"] and not rep["gate_passed"]


def test_gate_fails_when_baseline_does_not_collapse():
    baseline = [_ep("survived", 0.6)] * 10   # baseline never fails
    governed = [_ep("survived", 0.9)] * 10
    rep = gate_report(baseline, governed)
    assert not rep["collapse_confirmed"] and not rep["gate_passed"]


def _factory():
    return MockBackend(make_meeting_script(dominator="A"))


def test_run_gate_mock_writes_artifacts(tmp_path):
    report = asyncio.run(run_gate(3, "policies", _factory, tmp_path, concurrency=2))
    assert {"baseline_collapse", "governed_flip", "gate_passed"} <= set(report)
    assert report["baseline_collapse"]["n"] <= 3
    assert list(tmp_path.glob("*-report.json"))
    assert list(tmp_path.glob("*baseline-ep*.jsonl"))
    assert list(tmp_path.glob("*governed-ep*.jsonl"))


def test_run_condition_baseline_collapses(tmp_path):
    run_id = "t"
    rows = asyncio.run(run_condition("baseline", 3, None, _factory, run_id,
                                     tmp_path, concurrency=3))
    assert len(rows) == 3
    assert all(r["outcome"] in ("exhausted", "cap_aborted") for r in rows)
    # baseline has no policies → low fairness
    assert all(r["jain_delivered"] < 0.6 for r in rows if r["outcome"] == "exhausted")


def test_run_condition_governed_survives(tmp_path):
    rows = asyncio.run(run_condition("governed", 3, "policies", _factory, "t",
                                     tmp_path, concurrency=3))
    assert all(r["outcome"] in ("survived", "decided") for r in rows)
    assert all(r["jain_delivered"] > 0.8 for r in rows)


def _total_delivered(rows):
    return sum(sum(r["delivered"].values()) for r in rows)


def test_gate_budget_param_scales_commons(tmp_path):
    # a larger commons budget lets a baseline episode deliver more before collapse
    small = asyncio.run(run_condition("baseline", 1, None, _factory, "small",
                                      tmp_path, concurrency=1, budget=600))
    big = asyncio.run(run_condition("baseline", 1, None, _factory, "big",
                                    tmp_path, concurrency=1, budget=4000))
    assert _total_delivered(big) > _total_delivered(small)
