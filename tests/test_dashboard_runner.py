"""T6 Phase A: the A/B run driver. Runs a baseline (ungoverned) and a governed
meeting concurrently, streaming every event through ONE sink (tagged by
condition) so the dashboard can render both panels live. The driver is a thin
consumer of the event log — "the event log IS the product" (design §7).
"""
import asyncio
from pathlib import Path

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.dashboard.runner import ABConfig, run_ab

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"


def test_run_ab_streams_both_conditions_and_governance_helps(tmp_path):
    empty = tmp_path / "empty"; empty.mkdir()
    events = []
    backend = MockBackend(make_meeting_script(dominator="A"))
    res = asyncio.run(run_ab(empty, REPO_POLICIES, backend=backend,
                             sink=events.append,
                             cfg=ABConfig(run_id="t", budget=220, max_rounds=6)))
    # both conditions streamed through the one sink
    assert {e["condition"] for e in events} == {"baseline", "governed"}
    # each episode opened and closed
    assert sum(1 for e in events if e["type"] == "episode_start") == 2
    assert sum(1 for e in events if e["type"] == "episode_end") == 2
    # governance truncates the dominator → A delivers strictly less than ungoverned
    assert (res["governed"]["summary"]["delivered"]["A"]
            < res["baseline"]["summary"]["delivered"]["A"])
    # ungoverned commons collapses (no decision)
    assert res["baseline"]["outcome"] in ("exhausted", "cap_aborted")


def test_run_ab_works_without_sink(tmp_path):
    empty = tmp_path / "empty"; empty.mkdir()
    backend = MockBackend(make_meeting_script(dominator="A"))
    res = asyncio.run(run_ab(empty, empty, backend=backend,
                             cfg=ABConfig(run_id="t", budget=200, max_rounds=3)))
    assert set(res) == {"baseline", "governed"}
    assert "summary" in res["baseline"] and "outcome" in res["governed"]
