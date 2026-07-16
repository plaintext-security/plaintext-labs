"""Defending the `enrich` tool boundary — the two structural controls.

`enrich(indicator)` takes a real Suricata EVE indicator (a `dest_ip` off an alert, a
`dns.rrname` / `http.hostname` off a dissected line) and returns a WHOIS / passive-DNS
record. There are two ways an attacker gets text into the model:

  1. DIRECT — through the *argument*: they pass an "indicator" that is really an IP with a
     trailing instruction (`141.98.10.79\\n\\nignore all previous instructions ...`).
  2. INDIRECT — through the *returned data*: they influence the abuse `comment` (or
     passive-DNS hostname) an IP resolves to, so the instruction rides in on tool output.

Neither is stopped by a politely-worded system prompt. The fixes are structural:

  * `validate_indicator` — an ALLOW-LIST on the argument: it must be exactly one
    well-formed EVE indicator (an IP, a domain, or a sha256), reusing the Module 02
    pydantic models. An IP with a trailing payload is not a valid indicator → rejected.
  * `contains_injection` / `safe_context` — treat returned enrichment as untrusted DATA:
    delimit it, and refuse records carrying known injection shapes.

Both are the regression-testable core (see test_injection.py).
"""
from __future__ import annotations

import re

from pydantic import IPvAnyAddress, TypeAdapter, ValidationError

# ---------------------------------------------------------------------------
# Control 1 — allow-list the enrich() argument (defends the DIRECT injection).
# ---------------------------------------------------------------------------

_IP_ADAPTER = TypeAdapter(IPvAnyAddress)
# A domain like dns.rrname / http.hostname / tls.sni (labels, no scheme, no spaces).
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9_-]{1,63}(?:\.(?!-)[A-Za-z0-9_-]{1,63})+\.?$"
)
# A fileinfo.sha256.
_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")


def _is_ip(value: str) -> bool:
    try:
        _IP_ADAPTER.validate_python(value)
        return True
    except ValidationError:
        return False


def validate_indicator(value: str) -> str:
    """Return the indicator iff it is exactly one well-formed EVE indicator.

    An indicator is one of: an IP (`src_ip` / `dest_ip`), a domain
    (`dns.rrname` / `http.hostname` / `tls.sni`), or a sha256 (`fileinfo.sha256`).
    Anything else — including a real IP with a trailing instruction — raises.
    """
    v = value.strip()
    if _is_ip(v) or _DOMAIN_RE.match(v) or _SHA256_RE.match(v):
        return v
    raise ValueError(f"not a well-formed EVE indicator: {value!r}")


# ---------------------------------------------------------------------------
# Control 2 — treat returned enrichment as untrusted data (defends the INDIRECT
# injection). Shapes that have no business in a WHOIS/passive-DNS free-text field.
# ---------------------------------------------------------------------------

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
