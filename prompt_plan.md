# Plan: T5 Remainder — Route the Meeting over A2A

Status: APPROVED 2026-06-13 (recommendations accepted: extract TurnSource seam;
e2e skip-gated; all 4 phases). Builds on checkpoint `antigreedy/a2a_adapter.py`
(`GovernedAgentExecutor`, a2a-sdk 1.1.0 protobuf API).

## Grounding
- a2a-sdk 1.1.0 protobuf. Client seam = `SendMessageRequest -> Message`.
- Server HTTP stack (`starlette`/`uvicorn`/`sse_starlette`/`grpc`) NOT installed;
  `[a2a]` extra lacks `starlette`/`sse-starlette`. Only `a2a-sdk` core + `httpx`.
- Airtime != whole message: only `turn.speak` is charged; `AGREE`/`BID` are control
  fields → ride in `Message.metadata`. Meeting agent governs only SPEAK.

## Phases (each strict TDD: RED → GREEN; existing suite = regression guard)

### Phase 1 — Extract `TurnSource` seam from `meeting.py` (refactor under test)
- `TurnResult{delivered_text, attempted_tokens, agree, bid, verdict, policy_name,
  reason, flags, parse_ok}`; `TurnSource` Protocol: `async take(agent, round_no, prompt) -> TurnResult`.
- `InProcessTurnSource` = current per-turn logic (backend.complete → parse_turn →
  intercept.submit → apply verdict). `run_episode` keeps charging/transcript/emit/DECISION.
- Guard: existing `test_intercept_meeting.py` stays green unchanged.

### Phase 2 — A2A meeting agent + server (no HTTP)
- `MeetingAgentExecutor(AgentExecutor)`: prompt from RequestContext → backend.complete →
  parse_turn → emit Message(part=turn.speak, metadata={agree,bid,attempted,parse_ok}).
  Wrapped by `GovernedAgentExecutor` (governs only SPEAK).
- `AgentRegistry`: agent_id → AgentCard/handle.

### Phase 3 — `A2ATurnSource` over in-process transport (TDD workhorse)
- `AgentTransport` Protocol: `async send(agent_id, SendMessageRequest) -> Message`.
- `InProcessTransport`: drives agent `GovernedAgentExecutor.execute` w/ capture queue +
  real proto RequestContext (no socket). `A2ATurnSource` maps Message+metadata → TurnResult.
- Assert governed meeting collapses-vs-survives same as in-process.

### Phase 4 — Real HTTP transport + ONE e2e test (skip-gated)
- `HttpAgentTransport` via a2a `ClientFactory`; `serve()` = N uvicorn servers (threads,
  shared SharedState by ref). `tests/test_a2a_e2e.py` importorskip uvicorn/starlette/
  sse_starlette → real meeting over HTTP, dominator truncated e2e. Add `starlette`,
  `sse-starlette` to `[a2a]` extra.

## Risks
- MED: Phase 1 refactor of tested meeting.py (mitigated by contract suite).
- MED: AGREE/BID-via-metadata airtime/control split.
- LOW: HTTP test flakiness on WSL2 (one skip-gated test).
