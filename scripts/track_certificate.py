#!/usr/bin/env python3
"""Mint and verify a Plaintext **track-completion certificate** (the T7 credential).

A track certificate is the next layer up from the per-lab completion receipts that
`grade.py` writes (see `verify_receipt.py`). Where a *receipt* attests to one lab, a
*certificate* attests to a whole **track**: every module lab plus the capstone, each
proven by a valid receipt, aggregated and re-digested into one portfolio artifact.

This module builds directly ON `verify_receipt.py` — it reuses the same digest/HMAC
scheme and receipt-validation logic rather than re-implementing it, so a certificate is
exactly "a bundle of receipts the verifier already trusts, plus a roll-up digest."

    # Mint: gather receipts and emit certificate.json for a track
    python3 scripts/track_certificate.py mint \
        --track 00-foundations \
        --name "Ada Lovelace" \
        --receipts path/to/portfolio/00-foundations \
        --out certificate.json

    # Verify: what the public verification page / a reviewer runs
    python3 scripts/track_certificate.py verify certificate.json
    GRADER_HMAC_KEY=... python3 scripts/track_certificate.py verify certificate.json

    # Badge: a self-contained SVG + Markdown snippet for your portfolio README
    python3 scripts/track_certificate.py badge certificate.json --out-svg badge.svg

Open-repo honesty (identical to the receipt model): the digest proves the certificate is
internally consistent and unedited, and that every embedded receipt is itself unedited.
It does NOT prove grading was proctored — answer keys live in this open repo. The HMAC
adds tamper-evidence verifiable only by a holder of the key the learner never had (a
future server-side grader). A real anti-cheat credential needs that server-side grading.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

# Build ON the existing receipt verifier rather than duplicating its scheme.
from verify_receipt import sha256_text, verify_receipt_dict


# Human-readable track titles for the badge label (id -> display name).
TRACK_TITLES = {
    "00-foundations": "Foundations",
    "01-offensive": "Offensive Security",
    "02-defensive": "Defensive Security",
    "03-forensics": "Digital Forensics",
    "04-malware": "Malware Analysis",
    "05-cloud": "Cloud Security",
    "06-active-directory": "Active Directory",
    "07-endpoint-hardening": "Endpoint Hardening",
    "08-cryptography": "Cryptography",
    "09-python-for-security": "Python for Security",
    "10-automation": "Security Automation",
    "11-ztna": "Zero Trust",
    "12-ai-augmented-ops": "AI-Augmented Ops",
}


def discover_receipts(root: Path) -> list[Path]:
    """Find every receipt.json under a directory (one per lab + the capstone)."""
    return sorted(root.rglob("receipt.json"))


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_badge_svg(track: str, valid: bool = True) -> str:
    """A self-contained shields.io-style SVG badge — no external image dependency.

    Left cell: "Plaintext". Right cell: the track name, green when the certificate
    verifies. Widths are approximate (6px/char) — fine for a flat badge.
    """
    label = "Plaintext"
    msg = TRACK_TITLES.get(track, track)
    color = "#3fb950" if valid else "#8b949e"  # plaintext terminal-green / muted
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


def mint(args: argparse.Namespace) -> int:
    root = Path(args.receipts)
    if not root.is_dir():
        print(f"error: --receipts {root} is not a directory", file=sys.stderr)
        return 2

    receipt_paths = discover_receipts(root)
    if not receipt_paths:
        print(f"error: no receipt.json found under {root}", file=sys.stderr)
        return 2

    receipts: list[dict] = []
    invalid: list[str] = []
    for p in receipt_paths:
        data = json.loads(p.read_text())
        result = verify_receipt_dict(data, key=os.environ.get("GRADER_HMAC_KEY"))
        if not result.digest_ok:
            invalid.append(f"{p}: digest mismatch (receipt was edited)")
            continue
        if result.hmac_checked and not result.hmac_ok:
            invalid.append(f"{p}: HMAC invalid")
            continue
        if not result.all_checks_passed:
            invalid.append(f"{p}: not all checks passed")
            continue
        receipts.append(
            {
                "lab": data.get("lab"),
                "completed_at": data.get("completed_at"),
                "digest": data.get("digest"),
            }
        )

    if invalid:
        print("error: cannot mint — these receipts are not valid/complete:", file=sys.stderr)
        for line in invalid:
            print(f"  - {line}", file=sys.stderr)
        return 1

    labs = sorted({r["lab"] for r in receipts if r["lab"]})
    cert = {
        "credential": "Plaintext Track Certificate",
        "track": args.track,
        "learner": args.name,
        "issued_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "labs_completed": len(labs),
        "receipts": sorted(receipts, key=lambda r: r["lab"] or ""),
        "certificate_version": 1,
    }
    cert["digest"] = sha256_text(json.dumps(cert, sort_keys=True))
    key = os.environ.get("GRADER_HMAC_KEY")
    if key:
        cert["hmac"] = hmac.new(
            key.encode(), json.dumps(cert, sort_keys=True).encode(), hashlib.sha256
        ).hexdigest()

    out = Path(args.out)
    out.write_text(json.dumps(cert, indent=2) + "\n")
    print(f"Minted {cert['credential']} for {args.name}")
    print(f"  Track:  {args.track}")
    print(f"  Labs:   {len(labs)} ({', '.join(labs)})")
    print(f"  Digest: {cert['digest']}")
    if key:
        print("  HMAC:   added (verifiable by the grader-key holder)")
    print(f"  Wrote:  {out} — commit it to your portfolio repo.")
    return 0


def verify(args: argparse.Namespace) -> int:
    cert = json.loads(Path(args.certificate).read_text())

    claimed_digest = cert.pop("digest", None)
    claimed_hmac = cert.pop("hmac", None)
    recomputed = sha256_text(json.dumps(cert, sort_keys=True))
    ok = claimed_digest == recomputed

    print(f"Credential: {cert.get('credential')}")
    print(f"Track:      {cert.get('track')}")
    print(f"Learner:    {cert.get('learner')}")
    print(f"Issued:     {cert.get('issued_at')}")
    print(f"Labs:       {cert.get('labs_completed')} completed")
    for r in cert.get("receipts", []):
        print(f"   - {r.get('lab')}  ({r.get('completed_at')})")
    print(f"Digest:     {'OK — unedited' if ok else 'MISMATCH — certificate was modified'}")

    key = os.environ.get("GRADER_HMAC_KEY")
    if key:
        if claimed_hmac is None:
            print("HMAC:       missing (certificate was made without a key)")
            ok = False
        else:
            payload = dict(cert)
            payload["digest"] = recomputed
            expected = hmac.new(
                key.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256
            ).hexdigest()
            hmac_ok = hmac.compare_digest(expected, claimed_hmac)
            print(f"HMAC:       {'OK — signed by grader key' if hmac_ok else 'INVALID'}")
            ok = ok and hmac_ok
    elif claimed_hmac:
        print("HMAC:       present but not checked (set GRADER_HMAC_KEY to verify)")

    print("\nResult:", "VALID" if ok else "INVALID")
    return 0 if ok else 1


def badge(args: argparse.Namespace) -> int:
    cert = json.loads(Path(args.certificate).read_text())
    result_payload = {k: v for k, v in cert.items() if k not in ("digest", "hmac")}
    recomputed = sha256_text(json.dumps(result_payload, sort_keys=True))
    valid = cert.get("digest") == recomputed
    track = cert.get("track", "")
    title = TRACK_TITLES.get(track, track)

    svg = render_badge_svg(track, valid=valid)
    out_svg = Path(args.out_svg)
    out_svg.write_text(svg)

    digest = cert.get("digest", "")
    print(f"Wrote badge: {out_svg}")
    print()
    print("Paste this into your portfolio README (point the link at where you host the cert):")
    print()
    print(f"![Plaintext {title} certificate]({out_svg.name})  ")
    print(f"**Plaintext {title} Track** — {cert.get('labs_completed', '?')} labs completed.  ")
    print(f"Certificate digest `{digest[:16]}…` · "
          f"verify: `python3 track_certificate.py verify certificate.json`")
    if not valid:
        print("\nWARNING: this certificate's digest does NOT verify — badge rendered muted.",
              file=sys.stderr)
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("mint", help="aggregate per-lab receipts into a track certificate")
    m.add_argument("--track", required=True, help="track id, e.g. 00-foundations")
    m.add_argument("--name", required=True, help="learner name to put on the certificate")
    m.add_argument("--receipts", required=True,
                   help="directory holding the track's per-lab receipt.json files")
    m.add_argument("--out", default="certificate.json", help="output path")
    m.set_defaults(func=mint)

    v = sub.add_parser("verify", help="re-verify a certificate.json (digest + receipts + HMAC)")
    v.add_argument("certificate")
    v.set_defaults(func=verify)

    b = sub.add_parser("badge", help="emit an SVG badge + README snippet for a certificate")
    b.add_argument("certificate")
    b.add_argument("--out-svg", default="badge.svg", help="output SVG path")
    b.set_defaults(func=badge)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
