"""E3: experiment history. Every dashboard run is persisted (config + full event
log) so the user can list past experiments and re-open one to replay it. Turns
one-shot demos into a logbook (PRD §12 E3)."""
import tempfile
from pathlib import Path

from antigreedy.dashboard.history import HistoryStore


def _events(condition, outcome):
    return [
        {"type": "episode_start", "condition": condition,
         "data": {"agents": ["A", "B"], "budget": 100}, "policy_set_hash": "h1"},
        {"type": "turn", "condition": condition,
         "data": {"agent_id": "A", "verdict": "modify"}, "policy_set_hash": "h1"},
        {"type": "episode_end", "condition": condition,
         "data": {"outcome": outcome, "commons_left": 5}},
    ]


def _store():
    return HistoryStore(Path(tempfile.mkdtemp(prefix="ag_hist_")))


def test_save_returns_summary_and_persists_full_record():
    s = _store()
    events = _events("baseline", "exhausted") + _events("governed", "survived")
    rec = s.save(mode="ab", events=events)
    assert rec["mode"] == "ab"
    assert rec["id"]
    assert rec["outcomes"] == {"baseline": "exhausted", "governed": "survived"}
    assert rec["policy_set_hash"] == "h1"
    assert rec["n_turns"] == 2
    # full record (with events) is retrievable by id
    full = s.get(rec["id"])
    assert full is not None and full["events"] == events


def test_list_is_newest_first_and_omits_events():
    s = _store()
    first = s.save(mode="ab", events=_events("governed", "survived"))
    second = s.save(mode="probe", events=_events("governed", "decided"))
    listed = s.list()
    assert [r["id"] for r in listed] == [second["id"], first["id"]]  # newest first
    assert all("events" not in r for r in listed)  # list view is lightweight
    assert listed[0]["mode"] == "probe"


def test_get_unknown_id_returns_none():
    assert _store().get("nope") is None


def test_survives_restart_reads_from_disk():
    d = Path(tempfile.mkdtemp(prefix="ag_hist_"))
    rec = HistoryStore(d).save(mode="live", events=_events("governed", "survived"))
    # a fresh store over the same dir sees the persisted run
    assert HistoryStore(d).get(rec["id"]) is not None
    assert HistoryStore(d).list()[0]["id"] == rec["id"]
