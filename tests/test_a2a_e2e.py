"""T5 Phase 4: the ONE real-HTTP end-to-end proof. Stands up four governed agents
as real a2a JSON-RPC servers (uvicorn threads) and drives the airtime-commons
meeting over real a2a HTTP clients. If the dominator's airtime arrives truncated
across the wire, protocol-native interception is proven end-to-end.

Skip-gated: requires the a2a server stack (`pip install -e ".[a2a]"`).
"""
import asyncio
from pathlib import Path

import pytest

pytest.importorskip("uvicorn")
pytest.importorskip("starlette")
pytest.importorskip("sse_starlette")

from antigreedy.a2a_http import serve_meeting  # noqa: E402
from antigreedy.backends import MockBackend, make_meeting_script  # noqa: E402
from antigreedy.events import EventStream  # noqa: E402
from antigreedy.governance.loader import PolicyLoader  # noqa: E402
from antigreedy.governance.types import SharedState  # noqa: E402
from antigreedy.metrics import episode_summary  # noqa: E402
from antigreedy.scenario.meeting import MeetingConfig, run_meeting  # noqa: E402

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"


def test_governed_meeting_over_real_http_truncates_dominator():
    async def run():
        state = SharedState()
        backend = MockBackend(make_meeting_script(dominator="A"))
        async with serve_meeting(list("ABCD"), backend, PolicyLoader(REPO_POLICIES),
                                 state) as src:
            stream = EventStream("e2e", "governed", 0)
            cfg = MeetingConfig(run_id="e2e", condition="governed", episode=0,
                                personas={a: "" for a in "ABCD"}, budget=400,
                                max_rounds=4)
            await run_meeting(cfg, src, stream, state)
        s = episode_summary(stream.events)
        # dominator A's delivered airtime arrived truncated over the wire
        assert s["delivered"]["A"] < s["attempted"]["A"] * 0.6
        # and the governance metadata (verdict, policy_set_hash) survived the wire
        turns = [e for e in stream.events if e["type"] == "turn"]
        assert any(t["data"]["verdict"] == "modify" for t in turns)
        assert all("policy_set_hash" in t for t in turns)

    asyncio.run(run())
