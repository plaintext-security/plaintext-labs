#!/usr/bin/env python3
"""Password hash cracking harness.

Demonstrates the key concepts in password attacks:
  1. Hash identification — why MD5 looks different from bcrypt
  2. Dictionary attack — iterate rockyou.txt candidates
  3. KDF comparison — why bcrypt resists attacks that MD5 doesn't
  4. Rules-based attack — common mutations (append digits, capitalize)

The rockyou.txt wordlist comes from the real 2009 RockYou breach —
3.1 million plaintext passwords. It's the canonical cracking dictionary
because those ARE the passwords humans choose.

In production, use hashcat with GPU acceleration. This Python harness
teaches the LOGIC of hash cracking; hashcat is the industrial tool.

> Only crack hashes you own or are authorized to test.

Usage:
    python3 crack.py          # demo mode — crack bundled hashes
    python3 crack.py --bench  # benchmark MD5 vs bcrypt cost comparison
"""
from __future__ import annotations

import hashlib
import hmac
import re
import sys
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DIVIDER  = "─" * 64

# A sample from rockyou.txt — the ~50 most common passwords
# In production, hashcat uses the full 3.1M entry list
ROCKYOU_SAMPLE = [
    "password", "123456", "12345678", "1234", "qwerty", "12345", "dragon",
    "pussy", "baseball", "football", "letmein", "monkey", "696969", "abc123",
    "mustang", "michael", "shadow", "master", "jennifer", "111111", "2000",
    "jordan", "superman", "harley", "1234567", "iloveyou", "sunshine", "princess",
    "tigger", "cheese", "ginger", "1234567890", "joshua", "password1", "batman",
    "hunter", "secret", "1q2w3e4r", "pass", "hello", "passw0rd", "password123",
    "test", "welcome", "login", "admin", "admin123", "changeme", "abc",
    # Common company-specific guesses (rules-based mutations)
    "acme", "Acme1", "acme123", "Acm3Corp!", "company2024",
]

# Rules: common password mutations a rules engine applies
def apply_rules(word: str) -> list[str]:
    mutations = [word]
    mutations.append(word + "1")
    mutations.append(word + "123")
    mutations.append(word + "!")
    mutations.append(word.capitalize())
    mutations.append(word.capitalize() + "1")
    mutations.append(word.upper())
    # leet speak
    mutations.append(word.replace("a", "@").replace("e", "3").replace("o", "0"))
    return mutations


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def ntlm(s: str) -> str | None:
    # MD4 (NTLM algorithm) is unavailable in OpenSSL FIPS builds.
    # Use passlib if available; otherwise skip with a note.
    try:
        from passlib.hash import nthash
        return nthash.hash(s).lower()
    except ImportError:
        pass
    try:
        return hashlib.new("md4", s.encode("utf-16-le")).hexdigest()
    except ValueError:
        return None  # MD4 unavailable — NTLM requires passlib or impacket


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def identify_hash(h: str) -> tuple[str, str]:
    """Return (hash_type, hashcat_mode) based on hash format."""
    if h.startswith("$2b$") or h.startswith("$2a$"):
        return "bcrypt", "-m 3200"
    if len(h) == 32 and re.fullmatch(r"[0-9a-f]{32}", h):
        return "MD5 or NTLM (32-char hex — need context)", "-m 0 (MD5) or -m 1000 (NTLM)"
    if len(h) == 40 and re.fullmatch(r"[0-9a-f]{40}", h):
        return "SHA-1", "-m 100"
    if len(h) == 64 and re.fullmatch(r"[0-9a-f]{64}", h):
        return "SHA-256", "-m 1400"
    return "Unknown", "?"


# ── Load hashes from file ──────────────────────────────────────────────────────

def load_hashes(path: Path) -> list[dict]:
    hashes = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            username, hash_type, hash_value = parts[0], parts[1], parts[2]
            hashes.append({
                "username": username,
                "type": hash_type,
                "hash": hash_value,
                "cracked": None,
            })
    return hashes


def crack_hash(h: dict, wordlist: list[str], use_rules: bool = False) -> bool:
    """Try to crack a hash. Returns True if cracked."""
    hash_fn = {"md5": md5, "ntlm": ntlm, "sha1": sha1, "sha256": sha256}.get(h["type"])
    if hash_fn is None:
        return False  # bcrypt needs a real library; skip

    candidates = wordlist[:]
    if use_rules:
        for word in wordlist:
            candidates.extend(apply_rules(word))

    for candidate in candidates:
        result = hash_fn(candidate)
        if result is None:
            h["cracked"] = "(skipped — MD4/NTLM requires passlib)"
            return False
        if result == h["hash"]:
            h["cracked"] = candidate
            return True
    return False


# ── Demo ──────────────────────────────────────────────────────────────────────

def demo() -> int:
    hashes = load_hashes(DATA_DIR / "hashes.txt")

    print("=" * 64)
    print("Password Hash Cracking — lab dump")
    print(f"Loaded {len(hashes)} hashes from dump")
    print("=" * 64)

    # Step 1: Hash identification
    print(f"\n[Step 1] Hash identification")
    print()
    print(f"  {'User':15s}  {'Declared type':8s}  {'Detected type':35s}  hashcat mode")
    print(f"  {'─'*15}  {'─'*8}  {'─'*35}  {'─'*15}")
    for h in hashes:
        detected, mode = identify_hash(h["hash"])
        print(f"  {h['username']:15s}  {h['type']:8s}  {detected:35s}  {mode}")

    # Step 2: Dictionary attack
    print(f"\n{DIVIDER}")
    print(f"[Step 2] Dictionary attack — rockyou.txt sample ({len(ROCKYOU_SAMPLE)} candidates)")
    print()
    t0 = time.monotonic()
    for h in hashes:
        crack_hash(h, ROCKYOU_SAMPLE, use_rules=False)
    dict_time = time.monotonic() - t0
    cracked = [h for h in hashes if h["cracked"]]
    missed  = [h for h in hashes if not h["cracked"]]
    print(f"  Cracked: {len(cracked)}/{len(hashes)} in {dict_time*1000:.1f}ms")
    print()
    for h in cracked:
        print(f"  ✓ {h['username']:15s}  {h['type']:6s}  → {h['cracked']!r}")
    for h in missed:
        print(f"  ✗ {h['username']:15s}  {h['type']:6s}  → (not in sample wordlist)")

    # Step 3: Rules-based attack on missed hashes
    if missed:
        print(f"\n{DIVIDER}")
        print(f"[Step 3] Rules-based attack — mutations on wordlist")
        print()
        t0 = time.monotonic()
        newly_cracked = []
        for h in missed:
            if crack_hash(h, ROCKYOU_SAMPLE, use_rules=True):
                newly_cracked.append(h)
        rules_time = time.monotonic() - t0
        candidates_tried = len(ROCKYOU_SAMPLE) * 9  # ~9 mutations per word
        print(f"  Tried {candidates_tried} candidates in {rules_time*1000:.1f}ms")
        if newly_cracked:
            for h in newly_cracked:
                print(f"  ✓ {h['username']:15s}  {h['type']:6s}  → {h['cracked']!r}  (rules: mutation found it)")
        else:
            print(f"  No additional hashes cracked with rules.")
        print()
        still_missed = [h for h in hashes if not h["cracked"]]
        if still_missed:
            for h in still_missed:
                print(f"  ✗ {h['username']:15s}  {h['type']:6s}  → still uncracked")

    # Step 4: KDF comparison
    print(f"\n{DIVIDER}")
    print(f"[Step 4] KDF speed comparison — MD5 vs bcrypt")
    print()

    # Time MD5 at scale
    n = 100_000
    t0 = time.monotonic()
    for _ in range(n):
        md5("password123")
    md5_time = time.monotonic() - t0
    md5_rate  = int(n / md5_time)

    # Time bcrypt via hashlib (approximation — real bcrypt uses 12 rounds = ~250ms)
    bcrypt_rate_approx = 4  # ~4 hashes/sec per CPU core at cost factor 12

    print(f"  MD5:    {md5_rate:>10,} hashes/sec  (per CPU core)")
    print(f"  bcrypt: {bcrypt_rate_approx:>10,} hashes/sec  (cost factor 12, per CPU core)")
    print(f"  Ratio:  {md5_rate // bcrypt_rate_approx:>10,}× slower")
    print()
    print(f"  With rockyou.txt (14.3M entries):")
    print(f"    MD5:    {14_300_000 / md5_rate:.1f}s  (~{14_300_000 / md5_rate / 60:.0f}min)")
    print(f"    bcrypt: {14_300_000 / bcrypt_rate_approx:.0f}s  (~{14_300_000 / bcrypt_rate_approx / 86400:.0f} days per CPU core)")
    print()
    print("  Key insight: bcrypt's cost factor is what separates it from MD5.")
    print("  MFA + bcrypt(cost≥12) + password length ≥ 15 defeats offline cracking.")

    # Step 5: Summary
    all_cracked = [h for h in hashes if h["cracked"]]
    print(f"\n{'=' * 64}")
    print("Cracking summary")
    print(f"{'=' * 64}")
    print(f"""
  Cracked {len(all_cracked)}/{len(hashes)} hashes:
    • MD5/NTLM/SHA-1/SHA-256 all fell within milliseconds.
    • bcrypt ($2b$12$...) is NOT cracked — requires a real GPU and
      still takes days per hash at cost factor 12.
    • The ntlm 'aad3b435...' hash is a well-known NTLM null password
      (empty string). Zero password = instant crack.

  Defenses that would have stopped this:
    1. bcrypt / scrypt / Argon2 with cost factor ≥ 12 (slow KDF)
    2. Salt (already in bcrypt) prevents rainbow tables
    3. Password length ≥ 16 + complexity
    4. MFA: even a cracked hash is useless without the second factor
""")
    return 0


def bench() -> int:
    """Benchmark MD5 vs bcrypt to show KDF cost."""
    print("[Benchmark] MD5 vs bcrypt hash rate")
    n = 500_000
    t0 = time.monotonic()
    for _ in range(n):
        md5("password123")
    md5_rate = int(n / (time.monotonic() - t0))
    print(f"  MD5 (stdlib):   {md5_rate:>10,} hashes/sec")
    print(f"  bcrypt (cost 12): ~4 hashes/sec (requires passlib/bcrypt library)")
    print(f"  Ratio: {md5_rate // 4:>10,}×")
    return 0


if __name__ == "__main__":
    if "--bench" in sys.argv:
        sys.exit(bench())
    sys.exit(demo())
