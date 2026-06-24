#!/usr/bin/env python3
"""Generate the inert PE fixtures for the YARA half of the corpus.

These are NOT real malware: each is a tiny file that starts with the `MZ`
magic so a real `yara` binary treats it as a PE, followed by a handful of
ASCII strings chosen to be either malicious (the Latrodectus loader's C2 domain
/ masquerade name) or benign. No executable code, no live sample, safe to
commit and safe in CI.

The Dockerfile/Makefile call this at image-build / detect time so the bytes
live in the container; the answer key for every fixture is data/labels.json.
"""
import os
import sys

# (filename, list-of-embedded-strings). Malicious vs benign is recorded ONLY in
# labels.json — the generator stays label-free so it can't leak ground truth.
FIXTURES = {
    # --- malicious: Latrodectus loader indicators (see Module 12 YARA rule) ----
    "pe-001-svchost32.exe":  ["This program cannot be run in DOS mode.", "workspacin.cloud", "svchost32", "/update.bin"],
    "pe-002-dropper.bin":    ["This program cannot be run in DOS mode.", "workspacin.cloud", "C:\\Windows\\Temp\\"],
    "pe-003-loader.exe":     ["This program cannot be run in DOS mode.", "svchost32", "/update.bin", "CreateRemoteThread"],

    # --- benign: ordinary software -------------------------------------------
    "pe-004-notepad.exe":    ["This program cannot be run in DOS mode.", "Notepad", "RegisterClassW"],
    "pe-005-7zip.exe":       ["This program cannot be run in DOS mode.", "7-Zip", "LZMA"],
    # BENIGN NEAR-MISS: a legit auto-updater that talks to a CDN and ships an
    # update.bin — a too-broad rule keying on "/update.bin" or "update" flags it.
    "pe-006-autoupdate.exe": ["This program cannot be run in DOS mode.", "update.example.com", "/update.bin", "AcmeUpdater"],
    # BENIGN NEAR-MISS: a packed-but-legitimate installer (high entropy section
    # names, UPX) — a rule keying on "packed == malicious" false-positives here.
    "pe-007-installer.exe":  ["This program cannot be run in DOS mode.", "UPX0", "UPX1", "Inno Setup"],
    "pe-008-svchost.exe":    ["This program cannot be run in DOS mode.", "svchost", "ServiceMain"],
}

MZ = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, strings in FIXTURES.items():
        body = MZ + b"\x00" * 48
        for s in strings:
            body += s.encode("latin-1") + b"\x00"
        body += b"\x00" * 16
        with open(os.path.join(out_dir, name), "wb") as fh:
            fh.write(body)
    print(f"Wrote {len(FIXTURES)} inert PE fixtures to {out_dir}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pe_fixtures")
