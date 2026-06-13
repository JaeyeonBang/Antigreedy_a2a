"""Run the A/B theater locally:  python -m antigreedy.dashboard [--port 8000]

Defaults to the deterministic MockBackend (no API key). Open the printed URL and
click ▶ Run to watch the ungoverned commons collapse next to the governed run.
"""
from __future__ import annotations

import argparse

import uvicorn

from antigreedy.dashboard.app import create_app


def main() -> None:
    ap = argparse.ArgumentParser(prog="antigreedy.dashboard")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    print(f"A/B theater → http://{args.host}:{args.port}")
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
