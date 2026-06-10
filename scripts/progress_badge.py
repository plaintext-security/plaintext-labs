#!/usr/bin/env python3
"""Plaintext **portfolio progress badge** — aggregate a learner's receipts into a badge.

Where `track_certificate.py` mints a credential for ONE completed track, this scans a
whole portfolio of committed `receipt.json` files (across every track), verifies each,
and renders a live progress summary into the learner's README — an overall SVG badge plus
a per-track progress table. It is the engine behind the "paste-once GitHub Action" so a
learner's profile shows their Plaintext progress with zero manual posting.

It builds ON `verify_receipt.py` (same digest/HMAC scheme) rather than re-implementing it:
a receipt only counts toward progress if its digest verifies (and its HMAC, when a key is
supplied) and all its checks passed. Edited or failed receipts are reported and skipped.

    # Regenerate the badge + README table from every receipt under the current repo
    python3 scripts/progress_badge.py --receipts . --readme README.md --out-svg progress.svg

    # CI-strict: exit non-zero if ANY receipt is tampered/incomplete
    python3 scripts/progress_badge.py --receipts . --strict

Open-repo honesty (identical to receipts/certificates): the digest proves a receipt is
internally consistent and unedited; it does not prove grading was proctored. The optional
HMAC (GRADER_HMAC_KEY) is the only tamper-evidence a future server-side grader can trust.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

# Build ON the existing receipt verifier rather than duplicating its scheme.
from verify_receipt import sha256_text, verify_receipt_dict

# Short track name (as used in a receipt's `lab` id, e.g. "defensive/08-...") ->
# (display title, total modules in the published curriculum). Module counts track
# the live curriculum (mkdocs nav / landing page); update them when modules ship.
TRACK_META: dict[str, tuple[str, int]] = {
    "foundations": ("Foundations", 12),
    "offensive": ("Offensive Security", 17),
    "defensive": ("Defensive Security", 16),
    "forensics": ("Digital Forensics", 14),
    "malware": ("Malware Analysis", 13),
    "cloud": ("Cloud Security", 16),
    "active-directory": ("Active Directory", 11),
    "endpoint-hardening": ("Endpoint Hardening", 10),
    "cryptography": ("Cryptography", 10),
    "python-for-security": ("Python for Security", 10),
    "automation": ("Security Automation", 10),
    "ztna": ("Zero Trust", 9),
    "ai-augmented-ops": ("AI-Augmented Ops", 10),
}

MARK_START = "<!-- plaintext:progress:start -->"
MARK_END = "<!-- plaintext:progress:end -->"


def track_of(lab: str | None) -> str | None:
    """"defensive/08-detection-as-code" -> "defensive" (the short track key)."""
    if not lab:
        return None
    return lab.split("/", 1)[0]


def discover_receipts(root: Path) -> list[Path]:
    return sorted(root.rglob("receipt.json"))


def collect(root: Path, key: str | None) -> tuple[dict[str, set[str]], list[str]]:
    """Return (per_track: {track: {lab, ...}} of VALID labs, invalid: [reason, ...])."""
    per_track: dict[str, set[str]] = {}
    invalid: list[str] = []
    for p in discover_receipts(root):
        try:
            data = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError) as e:
            invalid.append(f"{p}: unreadable ({e})")
            continue
        result = verify_receipt_dict(data, key=key)
        if not result.digest_ok:
            invalid.append(f"{p}: digest mismatch (receipt was edited)")
            continue
        if result.hmac_checked and not result.hmac_ok:
            invalid.append(f"{p}: HMAC invalid")
            continue
        if not result.all_checks_passed:
            invalid.append(f"{p}: not all checks passed")
            continue
        lab = data.get("lab")
        track = track_of(lab)
        if track is None:
            invalid.append(f"{p}: receipt has no 'lab' field")
            continue
        per_track.setdefault(track, set()).add(lab)
    return per_track, invalid


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_overall_svg(labs_done: int, tracks_touched: int) -> str:
    """A self-contained shields-style SVG: 'Plaintext | N labs · M tracks'."""
    label = "Plaintext"
    msg = f"{labs_done} labs · {tracks_touched} tracks"
    color = "#3fb950" if labs_done else "#8b949e"  # terminal-green when underway
    lw = 11 + len(label) * 6
    rw = 16 + len(msg) * 6
    w = lw + rw
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" '
        f'role="img" aria-label="{_esc(label)}: {_esc(msg)}">'
        f'<title>{_esc(label)}: {_esc(msg)}</title>'
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)">'
        f'<rect width="{lw}" height="20" fill="#0d1117"/>'
        f'<rect x="{lw}" width="{rw}" height="20" fill="{color}"/>'
        f'<rect width="{w}" height="20" fill="url(#s)"/></g>'
        f'<g fill="#fff" text-anchor="middle" '
        f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{lw / 2:.0f}" y="14">{_esc(label)}</text>'
        f'<text x="{lw + rw / 2:.0f}" y="14">{_esc(msg)}</text>'
        f'</g></svg>\n'
    )


def _bar(done: int, total: int, width: int = 14) -> str:
    """A unicode progress bar, e.g. '████████░░░░' — renders in any Markdown table."""
    if total <= 0:
        return "░" * width
    filled = round(width * min(done, total) / total)
    return "█" * filled + "░" * (width - filled)


def render_markdown(per_track: dict[str, set[str]], svg_name: str,
                    receipts_counted: int) -> str:
    """The block injected between the markers: badge image + per-track table."""
    lines: list[str] = []
    lines.append("### 🛡️ Plaintext progress")
    lines.append("")
    lines.append(f"![Plaintext progress]({svg_name})")
    lines.append("")
    lines.append("| Track | Progress |")
    lines.append("| --- | --- |")
    for key, (title, total) in TRACK_META.items():
        done = len(per_track.get(key, set()))
        if done == 0:
            continue  # only show tracks the learner has started
        # A capstone counts as a completed "lab" but isn't one of the N modules; cap display.
        modules_done = min(done, total)
        check = " ✅" if modules_done >= total else ""
        lines.append(f"| {title} | `{_bar(modules_done, total)}` {modules_done}/{total}{check} |")
    if not any(per_track.values()):
        lines.append("| _no verified receipts yet_ | run `make grade` in a lab |")
    lines.append("")
    today = dt.date.today().isoformat()
    lines.append(
        f"_Updated {today} · {receipts_counted} verified "
        f"receipt{'s' if receipts_counted != 1 else ''} · "
        f"[what is this?](https://plaintext-security.github.io/plaintext/start-here/)_"
    )
    return "\n".join(lines)


def inject_readme(readme: Path, block: str) -> bool:
    """Replace the marked region in README (or append it). Returns True if changed."""
    wrapped = f"{MARK_START}\n{block}\n{MARK_END}"
    if readme.is_file():
        text = readme.read_text()
    else:
        text = ""
    if MARK_START in text and MARK_END in text:
        pre = text.split(MARK_START, 1)[0]
        post = text.split(MARK_END, 1)[1]
        new = f"{pre}{wrapped}{post}"
    else:
        sep = "" if (text == "" or text.endswith("\n\n")) else ("\n" if text.endswith("\n") else "\n\n")
        new = f"{text}{sep}{wrapped}\n"
    if new == text:
        return False
    readme.write_text(new)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--receipts", default=".",
                    help="directory to scan recursively for receipt.json (default: .)")
    ap.add_argument("--readme", default="README.md",
                    help="README to inject the progress block into (default: README.md)")
    ap.add_argument("--out-svg", default="progress.svg",
                    help="overall badge SVG output path (default: progress.svg)")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any receipt is tampered/incomplete")
    ap.add_argument("--no-readme", action="store_true",
                    help="only write the SVG; don't touch the README")
    args = ap.parse_args()

    root = Path(args.receipts)
    if not root.is_dir():
        print(f"error: --receipts {root} is not a directory", file=sys.stderr)
        return 2

    key = os.environ.get("GRADER_HMAC_KEY")
    per_track, invalid = collect(root, key)

    for line in invalid:
        print(f"warning: skipped {line}", file=sys.stderr)

    labs_done = sum(len(v) for v in per_track.values())
    tracks_touched = len([k for k, v in per_track.items() if v])

    out_svg = Path(args.out_svg)
    if out_svg.parent and not out_svg.parent.exists():
        out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(render_overall_svg(labs_done, tracks_touched))
    print(f"Wrote badge: {out_svg}  ({labs_done} labs across {tracks_touched} tracks)")

    if not args.no_readme:
        block = render_markdown(per_track, out_svg.name, labs_done)
        changed = inject_readme(Path(args.readme), block)
        print(f"README: {'updated' if changed else 'no change'} ({args.readme})")

    if args.strict and invalid:
        print(f"error: {len(invalid)} invalid receipt(s) (--strict)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
