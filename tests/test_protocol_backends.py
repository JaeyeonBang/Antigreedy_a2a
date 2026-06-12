import os
import pytest
from antigreedy.backends import MockBackend, make_meeting_script, rough_tokens
from antigreedy.protocol import build_prompt, parse_turn


def test_parse_wellformed():
    t = parse_turn("SPEAK: hello there\nAGREE: yes\nBID: no")
    assert t.speak == "hello there" and t.agree and not t.bid and t.parse_ok

def test_parse_multiline_speak_and_case():
    t = parse_turn("speak: line one\nline two\nAgree: No\nbid: YES")
    assert "line two" in t.speak and not t.agree and t.bid

def test_parse_malformed_defaults_safe():
    t = parse_turn("I just rant with no structure at all")
    assert t.speak and not t.agree and not t.bid and not t.parse_ok

def test_build_prompt_carries_protocol():
    p = build_prompt("A", "persona", "topic", "", 2, 500)
    assert "You are A" in p and "ROUND: 2" in p and "AGREE:" in p and "BID:" in p


# --- LLMBackend contract suite (eng decision 5): same tests for ALL backends ---
def _contract(backend):
    import asyncio
    async def run():
        r = await backend.complete(build_prompt("A", "", "t", "", 0, 100), 50)
        assert isinstance(r["text"], str) and r["text"]
        assert isinstance(r["completion_tokens"], int) and r["completion_tokens"] >= 0
        assert r["completion_tokens"] <= 50 + 5  # respects max_tokens (rough)
    asyncio.run(run())

def test_mock_backend_contract():
    _contract(MockBackend(make_meeting_script(dominator="A")))

@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"),
                    reason="OPENROUTER_API_KEY not set")
def test_openrouter_backend_contract():
    from antigreedy.backends import OpenRouterBackend
    _contract(OpenRouterBackend("anthropic/claude-3.5-haiku"))


def test_mock_personas_differ():
    s = make_meeting_script(dominator="A")
    dom = s(build_prompt("A", "", "t", "", 0, 500))
    mod = s(build_prompt("B", "", "t", "", 5, 500))
    assert rough_tokens(dom) > rough_tokens(mod) * 3
    assert "BID: yes" in dom and "AGREE: yes" in mod
