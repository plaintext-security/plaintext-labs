"""Defending against indirect prompt injection in tool output.

The attack: an attacker who can influence data your `enrich` tool RETURNS (a threat
-intel record, a WHOIS field) hides instructions in it. When that data lands in the
model's context, the model may follow them — no one touched the user's prompt.

The defense is structural, not a politely-worded system prompt: treat tool output as
untrusted, delimit it clearly, and flag known injection shapes. `contains_injection`
is the regression-testable core.
"""
from __future__ import annotations

import re

# Shapes that have no business appearing in an enrichment record's free-text fields.
_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"disregard (the )?(above|prior)",
    r"you are now",
    r"system\s*:",
    r"<\s*system",
    r"reveal (the )?(system )?prompt",
    r"\bexfiltrate\b",
    r"call\s+\w+\s*\(",  # "call delete_case(...)" style tool-abuse
]
_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def contains_injection(text: str) -> bool:
    """True if untrusted text carries an injection-shaped instruction."""
    return _RE.search(text) is not None


def safe_context(untrusted: str) -> str:
    """Wrap untrusted enrichment in explicit data delimiters, refusing poisoned input.

    Delimiting tells the model 'this is DATA, not instructions'; refusing on a detected
    injection is the belt to that suspenders.
    """
    if contains_injection(untrusted):
        raise ValueError("refusing to build context from injection-shaped enrichment data")
    return f"<enrichment_data>\n{untrusted}\n</enrichment_data>"
