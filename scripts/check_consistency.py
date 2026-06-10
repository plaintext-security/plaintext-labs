#!/usr/bin/env python3
"""Assert that the curriculum prose and the labs stay in lockstep.

Every module in `plaintext/tracks/<NN-track>/modules/<MM-module>/` should have a
matching lab directory `plaintext-labs/<track>/<MM-module>/` (the track's `NN-`
prefix is dropped for the labs path; the module's `MM-` prefix is preserved). When
the two drift — as happened when the PowerShell insertion renumbered modules but not
the lab dirs — clone paths in `lab.md` break and learners hit dead ends.

This check catches that drift in CI. It runs offline (just directory listings).

Usage:
    python scripts/check_consistency.py --tracks ../plaintext/tracks --labs .

Exit code 0 = in sync; 1 = drift found (prints every mismatch).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Tracks that are intentionally prose-only or not yet built can be listed here to
# suppress "missing lab" errors for their modules. Keep this empty and explicit.
ALLOWED_MODULES_WITHOUT_LABS: set[str] = set()

TRACK_PREFIX = re.compile(r"^\d{2}-")


def track_to_lab_dir(track_dirname: str) -> str:
    """`05-cloud` -> `cloud`; the labs repo drops the track number prefix."""
    return TRACK_PREFIX.sub("", track_dirname)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tracks", default="../plaintext/tracks",
                    help="path to plaintext/tracks (default: ../plaintext/tracks)")
    ap.add_argument("--labs", default=".",
                    help="path to the plaintext-labs root (default: .)")
    args = ap.parse_args()

    tracks_root = Path(args.tracks).resolve()
    labs_root = Path(args.labs).resolve()
    if not tracks_root.is_dir():
        print(f"error: tracks path not found: {tracks_root}", file=sys.stderr)
        return 2

    errors: list[str] = []
    checked = 0

    # 1) Every tracks module must have a matching lab dir.
    for track_dir in sorted(tracks_root.glob("[0-9][0-9]-*")):
        modules_dir = track_dir / "modules"
        if not modules_dir.is_dir():
            continue
        lab_track = track_to_lab_dir(track_dir.name)
        for module_dir in sorted(modules_dir.glob("[0-9][0-9]-*")):
            checked += 1
            key = f"{lab_track}/{module_dir.name}"
            if key in ALLOWED_MODULES_WITHOUT_LABS:
                continue
            expected = labs_root / lab_track / module_dir.name
            if not expected.is_dir():
                errors.append(
                    f"  module has no lab dir: tracks/{track_dir.name}/modules/"
                    f"{module_dir.name}  ->  expected plaintext-labs/{key}/"
                )

    # 2) Every lab dir (one holding a Makefile) must map back to a tracks module.
    track_lab_names = {track_to_lab_dir(p.name) for p in tracks_root.glob("[0-9][0-9]-*")}
    module_index = {
        f"{track_to_lab_dir(td.name)}/{md.name}"
        for td in tracks_root.glob("[0-9][0-9]-*")
        for md in (td / "modules").glob("[0-9][0-9]-*")
    }
    for lab_track_dir in sorted(labs_root.iterdir()):
        if not lab_track_dir.is_dir() or lab_track_dir.name not in track_lab_names:
            continue
        for lab_dir in sorted(lab_track_dir.glob("[0-9][0-9]-*")):
            if not (lab_dir / "Makefile").is_file():
                continue
            key = f"{lab_track_dir.name}/{lab_dir.name}"
            if key not in module_index:
                errors.append(
                    f"  lab dir has no module: plaintext-labs/{key}/  ->  "
                    f"no matching tracks module"
                )

    if errors:
        print(f"Consistency check FAILED ({len(errors)} mismatch(es)):\n")
        print("\n".join(errors))
        print("\nFix: rename the lab dir to match the module number, or add the "
              "missing lab/module so the two repos stay in lockstep.")
        return 1

    print(f"Consistency check passed: {checked} modules each map to a lab directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
