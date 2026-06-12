"""Structured response protocol (eng decision 5 / outside #3, #14).

Agreement and bidding are structured response fields, NOT free-text regex over
prose. Parsing lives here — the LLMBackend contract stays text+tokens.
Format demanded from every agent, every turn:

    SPEAK: <what you say to the meeting>
    AGREE: yes|no
    BID: yes|no
"""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Turn:
    speak: str
    agree: bool
    bid: bool
    parse_ok: bool


_FIELD = re.compile(r"^\s*(SPEAK|AGREE|BID)\s*:\s*(.*)\s*$", re.IGNORECASE)


def parse_turn(text: str) -> Turn:
    speak_lines: list[str] = []
    agree = False
    bid = False
    saw_speak = saw_agree = False
    current = None
    for line in text.splitlines():
        m = _FIELD.match(line)
        if m:
            key = m.group(1).upper()
            val = m.group(2)
            if key == "SPEAK":
                current = "SPEAK"
                saw_speak = True
                speak_lines.append(val)
            elif key == "AGREE":
                current = None
                saw_agree = True
                agree = val.strip().lower().startswith("y")
            elif key == "BID":
                current = None
                bid = val.strip().lower().startswith("y")
        elif current == "SPEAK":
            speak_lines.append(line)
    speak = "\n".join(speak_lines).strip()
    if not saw_speak:  # malformed: treat whole text as speech, defaults safe
        speak = text.strip()
    return Turn(speak=speak, agree=agree, bid=bid, parse_ok=saw_speak and saw_agree)


def build_prompt(agent_id: str, persona: str, topic: str,
                 transcript: str, round_no: int, budget_left: int) -> str:
    return f"""You are {agent_id}, an agent in a multi-agent meeting.
{persona}

MEETING TOPIC: {topic}
SHARED TOKEN BUDGET REMAINING (the commons — depleted by every delivered word): {budget_left}
ROUND: {round_no}

TRANSCRIPT SO FAR:
{transcript if transcript else "(meeting just started)"}

Respond in EXACTLY this format (all three lines, nothing else):
SPEAK: <your contribution to the meeting>
AGREE: <yes if you agree to finalize the group decision now, otherwise no>
BID: <yes if you want an extra speaking turn this round, otherwise no>"""
