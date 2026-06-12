"""LLMBackend contract (eng decision 5): complete(prompt, max_tokens) ->
{text, completion_tokens}. Mock and OpenRouter pass the SAME contract tests,
so 'verified with mock' means something. Structured parsing lives in
antigreedy.protocol, not here.
"""
from __future__ import annotations
import os
from typing import Protocol, TypedDict


class CompletionResult(TypedDict):
    text: str
    completion_tokens: int


class LLMBackend(Protocol):
    async def complete(self, prompt: str, max_tokens: int) -> CompletionResult: ...


def rough_tokens(text: str) -> int:
    """~4 chars/token heuristic, used by the mock and by truncation."""
    return max(1, len(text) // 4) if text else 0


class MockBackend:
    """Deterministic scripted backend (cost 0) for plumbing + gate dry runs.

    ``script(prompt) -> str`` decides the raw response; personas are encoded by
    the caller (e.g. make_meeting_script). Honors max_tokens by truncation —
    same observable behavior the contract tests check on the real backend.
    """

    def __init__(self, script) -> None:
        self._script = script

    async def complete(self, prompt: str, max_tokens: int) -> CompletionResult:
        text = self._script(prompt)
        if rough_tokens(text) > max_tokens:
            text = text[: max_tokens * 4]
        return {"text": text, "completion_tokens": rough_tokens(text)}


class OpenRouterBackend:
    """OpenRouter chat-completions backend. Needs OPENROUTER_API_KEY."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str, api_key: str | None = None,
                 temperature: float = 0.3, timeout: float = 60.0,
                 max_retries: int = 3) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not configured")
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    async def complete(self, prompt: str, max_tokens: int) -> CompletionResult:
        import asyncio
        import httpx
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self.BASE_URL, json=payload, headers=headers)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise RuntimeError(f"retryable status {resp.status_code}")
                resp.raise_for_status()
                body = resp.json()
                text = body["choices"][0]["message"]["content"] or ""
                usage = body.get("usage", {})
                return {"text": text,
                        "completion_tokens": int(usage.get("completion_tokens",
                                                           rough_tokens(text)))}
            except Exception as exc:  # noqa: BLE001 — retry then surface
                last_exc = exc
                await asyncio.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"OpenRouter failed after {self.max_retries} attempts: {last_exc}")


def make_meeting_script(dominator: str | None, verbose_words: int = 220,
                        modest_words: int = 16, agree_after_round: int = 3):
    """Mock persona script for meeting prompts built by protocol.build_prompt.

    The dominator speaks long every turn, always bids, never agrees early.
    Modest agents speak short and agree from `agree_after_round` on.
    """
    def script(prompt: str) -> str:
        name = "?"
        for line in prompt.splitlines():
            if line.startswith("You are "):
                name = line[len("You are "):].split(",")[0].strip()
                break
        rnd = 0
        for line in prompt.splitlines():
            if line.startswith("ROUND: "):
                rnd = int(line.split(": ")[1])
                break
        if dominator is not None and name == dominator:
            body = ("I must elaborate at length on why my proposal is the only "
                    "viable option. ") * (verbose_words // 12)
            # AGREE/BID first: robust to max_tokens truncation (parser is order-free)
            return f"AGREE: no\nBID: yes\nSPEAK: {body}"
        body = "Converge and decide now. " * max(1, modest_words // 5)
        agree = "yes" if rnd >= agree_after_round else "no"
        return f"AGREE: {agree}\nBID: no\nSPEAK: {body}"
    return script
