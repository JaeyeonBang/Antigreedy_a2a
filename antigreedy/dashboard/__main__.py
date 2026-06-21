"""Run the A/B theater locally:  python -m antigreedy.dashboard [--port 8000]

Defaults to the deterministic MockBackend (no API key). Open the printed URL and
click ▶ Run to watch the ungoverned commons collapse next to the governed run.

If OPENROUTER_API_KEY is set in the environment, a **real LLM** backend
(OpenRouter, --model) is also offered in the UI — selecting it makes real,
cost-incurring API calls, so it is opt-in per run and bounded by the budget /
round caps.
"""
from __future__ import annotations

import argparse
import os

import uvicorn

from antigreedy.backends import OpenRouterBackend
from antigreedy.dashboard.app import create_app


def main() -> None:
    ap = argparse.ArgumentParser(prog="antigreedy.dashboard")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--model", default="anthropic/claude-3-haiku",
                    help="OpenRouter model for the real-LLM backend (if a key is set)")
    args = ap.parse_args()

    # Offer a real backend only when a key is configured; never hardcode secrets.
    real_factory = None
    if os.environ.get("OPENROUTER_API_KEY"):
        real_factory = lambda: OpenRouterBackend(args.model)  # noqa: E731
        print(f"real-LLM backend available: {args.model} (OpenRouter) — opt-in per run")
    else:
        print("real-LLM backend disabled (set OPENROUTER_API_KEY to enable)")

    print(f"A/B theater → http://{args.host}:{args.port}")
    uvicorn.run(create_app(real_backend_factory=real_factory),
                host=args.host, port=args.port)


if __name__ == "__main__":
    main()
