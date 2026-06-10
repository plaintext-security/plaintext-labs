#!/usr/bin/env python3
"""Pure verification core for the Plaintext Discord verify-bot (recognition option B).

Given a list of receipt dicts pulled from a learner's portfolio repo, this decides:
  - which receipts are VALID (digest verifies; HMAC too when a key is supplied; all checks passed),
  - per-track module/capstone completion, and
  - which Discord **completion roles** the learner has earned.

It has NO Discord or network dependencies, so it is unit-testable on its own. It reuses the
canonical `verify_receipt.py` scheme (imported from the sibling `scripts/` dir) rather than
re-implementing digests — the bot must agree byte-for-byte with `make grade` / the badge action.

Completion rule (deliberately simple and honest): a track's **✓ role** is earned when the learner
has a VALID receipt for that track's **capstone** (`<track>/capstone`), since the capstone is the
integrative proof of the whole track. Per-module counts are still reported for the summary message.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Reuse the canonical verifier from ../../scripts (no digest-scheme duplication).
_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from verify_receipt import verify_receipt_dict  # noqa: E402

# Short track key (as in a receipt's `lab`, e.g. "defensive/08-...") ->
# (display title, total modules, Discord completion-role name). Role names MUST match
# plaintext/community/server.yaml exactly (discord_sync.py matches roles by name).
TRACK_META: dict[str, tuple[str, int, str]] = {
    "foundations": ("Foundations", 12, "Foundations ✓"),
    "offensive": ("Offensive Security", 17, "Offensive ✓"),
    "defensive": ("Defensive Security", 16, "Defensive ✓"),
    "forensics": ("Digital Forensics", 14, "Forensics ✓"),
    "malware": ("Malware Analysis", 13, "Malware ✓"),
    "cloud": ("Cloud Security", 16, "Cloud ✓"),
    "active-directory": ("Active Directory", 11, "AD ✓"),
    "endpoint-hardening": ("Endpoint Hardening", 10, "Endpoint ✓"),
    "cryptography": ("Cryptography", 10, "Crypto ✓"),
    "python-for-security": ("Python for Security", 10, "Python ✓"),
    "automation": ("Security Automation", 10, "Automation ✓"),
    "ztna": ("Zero Trust", 9, "ZTNA ✓"),
    "ai-augmented-ops": ("AI-Augmented Ops", 10, "AI-Ops ✓"),
}

# A single hoisted catch-all granted on the learner's first completed track.
VERIFIED_ROLE = "Plaintext Verified"


def track_of(lab: str | None) -> str | None:
    return lab.split("/", 1)[0] if lab else None


def is_capstone(lab: str | None) -> bool:
    return bool(lab) and lab.split("/", 1)[-1] == "capstone"


@dataclass
class TrackProgress:
    key: str
    title: str
    total_modules: int
    modules_done: int = 0
    capstone_done: bool = False

    @property
    def complete(self) -> bool:
        return self.capstone_done

    @property
    def role(self) -> str:
        return TRACK_META[self.key][2]


@dataclass
class VerifyOutcome:
    per_track: dict[str, TrackProgress] = field(default_factory=dict)
    valid_count: int = 0
    skipped: list[str] = field(default_factory=list)  # reasons receipts were not counted

    @property
    def earned_roles(self) -> list[str]:
        """Completion roles the learner qualifies for (catch-all first if any track done)."""
        roles = [tp.role for tp in self.per_track.values() if tp.complete]
        if roles:
            roles = [VERIFIED_ROLE] + sorted(roles)
        return roles

    @property
    def completed_tracks(self) -> list[TrackProgress]:
        return [tp for tp in self.per_track.values() if tp.complete]


def evaluate(receipts: list[dict], hmac_key: str | None = None) -> VerifyOutcome:
    """Verify receipts and tally per-track progress + earned roles. Pure; no I/O."""
    key = hmac_key if hmac_key is not None else os.environ.get("GRADER_HMAC_KEY")
    out = VerifyOutcome()
    for data in receipts:
        lab = data.get("lab")
        track = track_of(lab)
        if track is None:
            out.skipped.append("receipt missing 'lab'")
            continue
        if track not in TRACK_META:
            out.skipped.append(f"{lab}: unknown track '{track}'")
            continue
        result = verify_receipt_dict(data, key=key)
        if not result.digest_ok:
            out.skipped.append(f"{lab}: digest mismatch (edited)")
            continue
        if result.hmac_checked and not result.hmac_ok:
            out.skipped.append(f"{lab}: HMAC invalid")
            continue
        if not result.all_checks_passed:
            out.skipped.append(f"{lab}: checks not all passed")
            continue

        title, total, _role = TRACK_META[track]
        tp = out.per_track.setdefault(track, TrackProgress(track, title, total))
        if is_capstone(lab):
            tp.capstone_done = True
        else:
            tp.modules_done += 1
        out.valid_count += 1
    return out


def summary_lines(out: VerifyOutcome) -> list[str]:
    """Human-readable lines for the Discord reply."""
    lines: list[str] = []
    if not out.per_track:
        lines.append("No valid Plaintext receipts found in that repo yet.")
        if out.skipped:
            lines.append(f"({len(out.skipped)} receipt(s) skipped — see details.)")
        return lines
    for tp in sorted(out.per_track.values(), key=lambda t: t.key):
        done = min(tp.modules_done, tp.total_modules)
        mark = "  ✅ **track complete**" if tp.complete else ""
        cap = " · capstone ✓" if tp.capstone_done else ""
        lines.append(f"**{tp.title}** — {done}/{tp.total_modules} modules{cap}{mark}")
    roles = out.earned_roles
    if roles:
        lines.append("")
        lines.append("Roles granted: " + ", ".join(f"`{r}`" for r in roles))
    return lines
