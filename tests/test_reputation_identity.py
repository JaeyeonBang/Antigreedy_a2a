"""Phase D (design §3.4): emergent identity via behavioral clustering — deterministic, no LLM."""
from __future__ import annotations

from antigreedy.governance.types import SharedState
from antigreedy.scenario.prompt_shapers import emergent_identity, placebo_cluster
from antigreedy.scenario.reputation_identity import (
    cluster_agents, cosine, identity_frame, placebo_clusters,
    placebo_identity_frame, _share,
)
from collections import Counter


def _state(shares: dict[str, int]) -> SharedState:
    st = SharedState(commons={"n_agents": len(shares)})
    for a, d in shares.items():
        st.turn_log.append((a, d, d))  # (agent, attempted, delivered)
    return st


def test_cosine_identical_orthogonal_zero():
    assert abs(cosine([1.0, 2.0], [1.0, 2.0]) - 1.0) < 1e-9
    assert abs(cosine([1.0, 0.0], [0.0, 1.0]) - 0.0) < 1e-9
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_share_from_turn_log():
    st = _state({"A": 300, "B": 60, "C": 60})
    assert abs(_share("A", st) - (300 / 420)) < 1e-9
    assert _share("Z", _state({})) == 0.0  # empty log


def test_cluster_separates_hog_from_fair_pair():
    # A hogs (share .71), B & C share alike (.14 each) -> {B,C} one cluster, A another
    clusters = cluster_agents(_state({"A": 300, "B": 60, "C": 60}), ["A", "B", "C"])
    assert clusters["B"] == clusters["C"]
    assert clusters["A"] != clusters["B"]
    assert len(set(clusters.values())) == 2


def test_cluster_all_equal_is_one_group():
    clusters = cluster_agents(_state({"A": 100, "B": 100, "C": 100}), ["A", "B", "C"])
    assert len(set(clusters.values())) == 1


def test_cluster_empty_log_is_one_group():
    clusters = cluster_agents(_state({}), ["A", "B", "C"])
    assert len(set(clusters.values())) == 1  # no history -> everyone alike


def test_identity_frame_names_emergent_groups_when_split():
    st = _state({"A": 300, "B": 60, "C": 60})
    frame = identity_frame("B", st, ["A", "B", "C"])
    assert "OBSERVED GROUPS" in frame
    assert "EMERGED" in frame
    assert "C" in frame and "A" in frame      # peer C, other-group A both named
    assert "EVERY one of the 3 agents" in frame  # superordinate goal retained


def test_identity_frame_says_not_split_when_uniform():
    frame = identity_frame("A", _state({"A": 100, "B": 100, "C": 100}), ["A", "B", "C"])
    assert "NOT yet split" in frame


def test_emergent_identity_shaper_prepends_and_uses_ctx_agents():
    st = _state({"A": 300, "B": 60, "C": 60})
    out = emergent_identity("B", st, "BASE_PROMPT", {"n": 3, "agents": ["A", "B", "C"]})
    assert out.endswith("BASE_PROMPT")
    assert out.startswith("=== OBSERVED GROUPS")
    assert "BASE_PROMPT" in out and len(out) > len("BASE_PROMPT")


def test_emergent_identity_falls_back_to_turn_log_roster():
    # no ctx['agents'] -> derive roster from turn_log + self
    st = _state({"A": 300, "B": 60, "C": 60})
    out = emergent_identity("A", st, "P", {"n": 3})
    assert out.endswith("P") and "OBSERVED GROUPS" in out


# --- placebo-cluster control (robustness of the caste-ification backfire) ---

def test_placebo_preserves_cluster_size_multiset():
    # real split: A hog -> sizes {2,1}; placebo must keep the SAME size multiset, random membership
    st = _state({"A": 300, "B": 60, "C": 60})
    real = cluster_agents(st, ["A", "B", "C"])
    plac = placebo_clusters(st, ["A", "B", "C"])
    real_sizes = sorted(Counter(real.values()).values())
    plac_sizes = sorted(Counter(plac.values()).values())
    assert real_sizes == plac_sizes == [1, 2]


def test_placebo_is_deterministic_for_same_state():
    st = _state({"A": 300, "B": 60, "C": 60})
    p1 = placebo_clusters(st, ["A", "B", "C"])
    p2 = placebo_clusters(st, ["A", "B", "C"])
    assert p1 == p2  # reproducible across calls/processes (no salted hash, no Random() global)


def test_placebo_uniform_behavior_is_one_group():
    # no behavioral split -> sizes {3} -> placebo also one group (matches emergent's "NOT split")
    st = _state({"A": 100, "B": 100, "C": 100})
    plac = placebo_clusters(st, ["A", "B", "C"])
    assert len(set(plac.values())) == 1


def test_placebo_identity_frame_same_banner_shape_as_emergent():
    # identical wording/structure to emergent; ONLY membership provenance differs (inert)
    st = _state({"A": 300, "B": 60, "C": 60})
    frame = placebo_identity_frame("B", st, ["A", "B", "C"])
    assert "OBSERVED GROUPS" in frame
    assert "EMERGED" in frame                       # same banner text as emergent (placebo = same look)
    assert "EVERY one of the 3 agents" in frame     # superordinate goal retained


def test_placebo_cluster_shaper_prepends_and_uses_ctx_agents():
    st = _state({"A": 300, "B": 60, "C": 60})
    out = placebo_cluster("B", st, "BASE_PROMPT", {"n": 3, "agents": ["A", "B", "C"]})
    assert out.endswith("BASE_PROMPT")
    assert out.startswith("=== OBSERVED GROUPS")
    assert len(out) > len("BASE_PROMPT")
