"""Real-HTTP A2A transport (T5 Phase 4).

Serves each governed meeting agent as a real a2a JSON-RPC HTTP server (uvicorn
thread) and routes turns through real a2a clients — proving the interception is
protocol-native end-to-end (a remote client receives the truncated airtime over
the wire). This module is imported ONLY when the server stack is installed
(starlette/uvicorn/sse-starlette); the in-process path never needs it, so the
core stays dependency-light.

All agents share ONE InProcessTurnSource (one intercept + state) for parity with
the in-process loop. The orchestrator drives turns sequentially, so the shared
governance state is touched one turn at a time.
"""
from __future__ import annotations

import asyncio
import contextlib
import socket
import threading
from collections.abc import AsyncIterator

import httpx
import uvicorn
from starlette.applications import Starlette

from a2a.client import ClientConfig, ClientFactory
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentInterface, Message, SendMessageRequest,
)
from a2a.utils import TransportProtocol

from antigreedy.a2a_meeting import A2ATurnSource, MeetingAgentExecutor
from antigreedy.backends import LLMBackend
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.turnsource import InProcessTurnSource


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def build_agent_app(executor: AgentExecutor, base_url: str, name: str) -> Starlette:
    """A Starlette app exposing ``executor`` as a real a2a JSON-RPC agent."""
    card = AgentCard(
        name=name, description="antigreedy meeting agent", version="0.1.0",
        capabilities=AgentCapabilities(streaming=True),
        supported_interfaces=[AgentInterface(
            url=base_url, protocol_binding=TransportProtocol.JSONRPC,
            protocol_version="1.0")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"])
    handler = DefaultRequestHandler(executor, InMemoryTaskStore(), card)
    return Starlette(routes=create_jsonrpc_routes(handler, "/")
                     + create_agent_card_routes(card))


class HttpAgentTransport:
    """AgentTransport over real a2a HTTP clients (drop-in for InProcessTransport)."""

    def __init__(self, clients: dict[str, object]) -> None:
        self._clients = clients

    async def send(self, agent_id: str, request: SendMessageRequest) -> Message:
        async for resp in self._clients[agent_id].send_message(request):
            if resp.message is not None:
                return resp.message
        raise RuntimeError(f"agent {agent_id!r} returned no message over HTTP")


class _ServerThread:
    def __init__(self, app: Starlette, host: str, port: int) -> None:
        self._server = uvicorn.Server(
            uvicorn.Config(app, host=host, port=port, log_level="error"))
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    async def wait_started(self, timeout: float = 5.0) -> None:
        for _ in range(int(timeout / 0.02)):
            if self._server.started:
                return
            await asyncio.sleep(0.02)
        raise RuntimeError("uvicorn server did not start in time")

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)


@contextlib.asynccontextmanager
async def serve_meeting(agents: list[str], backend: LLMBackend, loader: PolicyLoader,
                        state: SharedState, *, max_tokens: int = 300,
                        host: str = "127.0.0.1") -> AsyncIterator[A2ATurnSource]:
    """Stand up N governed agent servers + clients, yield an A2ATurnSource the
    meeting orchestrator can drive over real HTTP. Cleans up on exit."""
    intercept = InProcessInterceptPoint(loader, state)
    source = InProcessTurnSource(backend, intercept, max_tokens=max_tokens)
    servers: dict[str, _ServerThread] = {}
    bases: dict[str, str] = {}
    for agent in agents:
        port = _free_port()
        bases[agent] = f"http://{host}:{port}"
        srv = _ServerThread(
            build_agent_app(MeetingAgentExecutor(agent, source), bases[agent], agent),
            host, port)
        srv.start()
        servers[agent] = srv
    hx = httpx.AsyncClient(timeout=30)
    try:
        for srv in servers.values():
            await srv.wait_started()
        factory = ClientFactory(ClientConfig(
            streaming=False, polling=False, httpx_client=hx))
        clients = {a: await factory.create_from_url(bases[a]) for a in agents}
        yield A2ATurnSource(HttpAgentTransport(clients), intercept.policy_set_hash())
    finally:
        await hx.aclose()
        for srv in servers.values():
            srv.stop()
