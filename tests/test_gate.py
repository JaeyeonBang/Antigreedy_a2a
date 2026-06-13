import asyncio
from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.gate import run_condition, run_gate


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
