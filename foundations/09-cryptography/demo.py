#!/usr/bin/env python3
"""
Cryptography Lab — exercise each primitive with openssl via subprocess.

Demonstrates:
  1. SHA-256 hash (integrity, not secrecy)
  2. AES-256-CBC encrypt + decrypt round-trip
  3. RSA keypair generation + encrypt + decrypt
  4. Read a real certificate (example.com) — issuer, subject, validity
  5. ECB pattern leak (the Adobe failure) vs salted hash (the fix)
  6. Bit-flip AES ciphertext — observe what happens on decryption

Usage: python3 demo.py   (inside container with openssl installed)
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

DIVIDER = "─" * 64
PASSPHRASE = "CryptoLab2024!"
MESSAGE = "Acme Corp Q4 revenue: $2.1B"


def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"[Step] {title}")
    print(DIVIDER)


def run(cmd: str, stdin: bytes | None = None) -> tuple[int, bytes]:
    r = subprocess.run(cmd, shell=True, capture_output=True, input=stdin)
    return r.returncode, r.stdout + r.stderr


def run_text(cmd: str, stdin: str | None = None) -> str:
    rc, out = run(cmd, stdin.encode() if stdin else None)
    return out.decode(errors="replace").strip()


def demo_sha256() -> None:
    section("1 — SHA-256: integrity guarantee, not secrecy")
    print()

    out = run_text(f"echo -n '{MESSAGE}' | openssl dgst -sha256")
    print(f"  Message: {MESSAGE!r}")
    print(f"  SHA-256: {out}")
    print()
    print("  Change one character and the digest changes completely (avalanche effect):")
    changed = MESSAGE.replace("$2.1B", "$2.2B")
    out2 = run_text(f"echo -n '{changed}' | openssl dgst -sha256")
    print(f"  Modified: {changed!r}")
    print(f"  SHA-256:  {out2}")
    print()
    print("  Why this proves integrity but not secrecy:")
    print("  SHA-256 is deterministic — anyone with the message can verify the hash.")
    print("  But the hash alone doesn't hide the message (it's not encrypted).")
    print()
    print("  CLI: echo -n 'hello' | openssl dgst -sha256")


def demo_aes() -> None:
    section("2 — AES-256-CBC: symmetric encryption round-trip")
    print()

    with tempfile.TemporaryDirectory() as tmp:
        pt = Path(tmp) / "plaintext.txt"
        ct = Path(tmp) / "ciphertext.bin"
        dec = Path(tmp) / "decrypted.txt"

        pt.write_text(MESSAGE)

        # Encrypt
        rc_enc, _ = run(
            f"openssl enc -aes-256-cbc -pbkdf2 -iter 100000 "
            f"-in {pt} -out {ct} -pass pass:{PASSPHRASE}"
        )
        ct_b64 = base64.b64encode(ct.read_bytes()).decode()
        print(f"  Ciphertext (base64): {ct_b64[:60]}…")

        # Decrypt
        rc_dec, _ = run(
            f"openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 "
            f"-in {ct} -out {dec} -pass pass:{PASSPHRASE}"
        )
        recovered = dec.read_text() if dec.exists() else "(decryption failed)"
        print(f"  Decrypted:           {recovered!r}")
        print()
        ok = "✓" if recovered == MESSAGE else "✗"
        print(f"  Round-trip: {ok}")
        print()
        print("  Note: AES-256-CBC with PBKDF2 is safe for this exercise, but")
        print("  AES-256-GCM (authenticated encryption) is preferred in production.")
        print()
        print("  CLI:")
        print(f"    openssl enc -aes-256-cbc -pbkdf2 -in plain.txt -out cipher.bin -pass pass:P@ss")
        print(f"    openssl enc -d -aes-256-cbc -pbkdf2 -in cipher.bin -out decrypted.txt -pass pass:P@ss")


def demo_rsa() -> None:
    section("3 — RSA: asymmetric key generation + encrypt/decrypt")
    print()

    with tempfile.TemporaryDirectory() as tmp:
        privkey = Path(tmp) / "private.pem"
        pubkey = Path(tmp) / "public.pem"
        ct_file = Path(tmp) / "rsa_ct.bin"
        dec_file = Path(tmp) / "rsa_dec.txt"

        short_msg = "Session key: 0xDEADBEEF"

        # Generate 2048-bit RSA key
        run(f"openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out {privkey} 2>/dev/null")
        run(f"openssl rsa -in {privkey} -pubout -out {pubkey} 2>/dev/null")

        # Encrypt with public key
        run(f"echo -n '{short_msg}' | "
            f"openssl rsautl -encrypt -pubin -inkey {pubkey} -out {ct_file} 2>/dev/null")
        ct_b64 = base64.b64encode(ct_file.read_bytes()).decode() if ct_file.exists() else "—"
        print(f"  Public key:  2048-bit RSA (anyone can encrypt)")
        print(f"  Ciphertext:  {ct_b64[:60]}…")

        # Decrypt with private key
        run(f"openssl rsautl -decrypt -inkey {privkey} -in {ct_file} -out {dec_file} 2>/dev/null")
        recovered = dec_file.read_text() if dec_file.exists() else "(failed)"
        ok = "✓" if recovered.strip() == short_msg else "✗"
        print(f"  Decrypted:   {recovered.strip()!r}  {ok}")
        print()
        print("  Key insight: only the private-key holder can decrypt.")
        print("  In TLS, RSA (or ECDH) is used to exchange a symmetric key,")
        print("  then AES is used for bulk data — combining both strengths.")
        print()
        print("  CLI:")
        print("    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out private.pem")
        print("    openssl rsa -in private.pem -pubout -out public.pem")
        print("    echo -n 'secret' | openssl rsautl -encrypt -pubin -inkey public.pem > ct.bin")
        print("    openssl rsautl -decrypt -inkey private.pem < ct.bin")


def demo_certificate() -> None:
    section("4 — Read a real certificate: issuer, subject, validity")
    print()

    out = run_text(
        "echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null "
        "| openssl x509 -noout -text 2>/dev/null "
        "| grep -E 'Subject:|Issuer:|Not Before:|Not After :' | head -10"
    )
    if out:
        for line in out.splitlines():
            print(f"  {line.strip()}")
        print()
        print("  Who vouches for it: the Issuer is the Certificate Authority (CA)")
        print("  that signed the cert. Your OS/browser trusts a list of root CAs;")
        print("  this chain is what makes TLS trustworthy (or attackable).")
    else:
        print("  (Network not available — run: openssl s_client -connect example.com:443 | openssl x509 -noout -text)")
    print()
    print("  CLI: echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates")


def demo_ecb_vs_salt() -> None:
    section("5 — The Adobe failure: ECB pattern leak vs salted hash")
    print()

    # A tiny "password database." Note that alice, dave, and frank all chose the
    # SAME password — exactly the situation that exposed Adobe's 153M rows.
    users = [
        ("alice", "sunshine"),
        ("bob",   "correcthorse"),
        ("carol", "password1"),
        ("dave",  "sunshine"),    # same as alice
        ("erin",  "correcthorse"),  # same as bob
        ("frank", "sunshine"),    # same as alice + dave
    ]

    # --- THE WRONG WAY: AES-ECB, one shared key, no salt (what Adobe did) ---
    # ECB encrypts each block independently, so identical plaintext blocks always
    # produce identical ciphertext blocks. With one reused key, two users who share
    # a password get byte-for-byte identical stored values — a visible pattern leak.
    # stdlib python has no AES, so we drive openssl (same tool the lab uses by hand).
    shared_key = "00112233445566778899aabbccddeeff"  # 128-bit key, hex

    def aes_ecb(plaintext: str) -> str:
        # Pad to the 16-byte AES block so a short password fills exactly one block.
        padded = plaintext.ljust(16, " ")
        cmd = (
            f"openssl enc -aes-128-ecb -K {shared_key} -nosalt -nopad "
            f"-A -base64"
        )
        rc, out = run(cmd, stdin=padded.encode())
        return out.decode(errors="replace").strip()

    print("  WRONG WAY — AES-128-ECB, one shared key, no salt (the Adobe scheme):")
    print(f"  {'user':<8} {'password':<14} {'stored ciphertext (base64)'}")
    print(f"  {'-'*8} {'-'*14} {'-'*30}")
    ecb_seen: dict[str, list[str]] = {}
    for user, pw in users:
        ct = aes_ecb(pw)
        ecb_seen.setdefault(ct, []).append(user)
        print(f"  {user:<8} {pw:<14} {ct}")
    print()
    leaked = {ct: us for ct, us in ecb_seen.items() if len(us) > 1}
    print("  --> Identical passwords produced IDENTICAL ciphertext. The leak:")
    for ct, us in leaked.items():
        print(f"      {', '.join(us)} share a password (same ciphertext, no cracking needed)")
    print("  This is the 'ECB penguin' in table form — and exactly how researchers")
    print("  clustered Adobe's 153M rows by password without decrypting a single one.")
    print()

    # --- THE RIGHT WAY: salted one-way hash, unique salt per user ---
    # Same passwords, but each row gets a fresh random salt before hashing, so the
    # stored value differs even when the password is identical. And it's one-way:
    # there is no key that turns the hash back into the password.
    print("  RIGHT WAY — PBKDF2-HMAC-SHA256, a fresh random salt per user (the fix):")
    print(f"  {'user':<8} {'password':<14} {'salt:hash (truncated)'}")
    print(f"  {'-'*8} {'-'*14} {'-'*30}")
    hash_seen: dict[str, list[str]] = {}
    for user, pw in users:
        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000)
        stored = f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(dk).decode()}"
        # Track only the hash half to show same-password rows now differ.
        hash_seen.setdefault(stored.split(":")[1], []).append(user)
        print(f"  {user:<8} {pw:<14} {stored[:46]}…")
    print()
    collisions = [us for h, us in hash_seen.items() if len(us) > 1]
    print("  --> Same passwords now produce DIFFERENT stored values "
          f"({'no collisions' if not collisions else 'collision!'}).")
    print("  The per-user salt breaks the pattern, and the hash is one-way:")
    print("  there is no key and no command that reverses it back to the password.")
    print()
    print("  THE LESSON: 'encrypted' (ECB, reused key, reversible, pattern-leaking)")
    print("  is NOT 'hashed + salted' (one-way, unique per user, no pattern). A")
    print("  password store must hash-and-salt — never encrypt.")
    print()
    print("  CLI (reproduce the leak by hand):")
    print("    printf 'sunshine        ' | openssl enc -aes-128-ecb -K %s -nosalt -nopad -A -base64" % shared_key)
    print("    # run it twice — identical output. That sameness is the whole bug.")


def demo_bit_flip() -> None:
    section("6 — Bit-flip attack: modify AES-CBC ciphertext, observe damage")
    print()

    with tempfile.TemporaryDirectory() as tmp:
        pt = Path(tmp) / "pt.txt"
        ct = Path(tmp) / "ct.bin"
        ct_flipped = Path(tmp) / "ct_flipped.bin"
        dec = Path(tmp) / "dec.txt"

        pt.write_text(MESSAGE)
        run(f"openssl enc -aes-256-cbc -pbkdf2 -iter 100000 "
            f"-in {pt} -out {ct} -pass pass:{PASSPHRASE}")

        # Flip byte 20 in the ciphertext
        ct_bytes = bytearray(ct.read_bytes())
        if len(ct_bytes) > 25:
            ct_bytes[20] ^= 0xFF
        ct_flipped.write_bytes(bytes(ct_bytes))

        rc, _ = run(f"openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 "
                    f"-in {ct_flipped} -out {dec} -pass pass:{PASSPHRASE} 2>/dev/null")
        result = dec.read_bytes() if dec.exists() else b"(decryption error)"
        printable = "".join(chr(b) if 32 <= b < 127 else "?" for b in result[:60])

        print(f"  Original ciphertext:     valid")
        print(f"  After flipping byte 20:  decrypts to garbage: {printable!r}")
        print()
        print("  CBC bit-flip: flipping bits in the nth ciphertext block corrupts")
        print("  that block AND predictably flips bits in the (n+1)th plaintext block.")
        print("  This is why CBC without authentication (like HMAC or GCM tag)")
        print("  is unsafe — an attacker can modify the message without knowing the key.")
        print()
        print("  AES-GCM adds an authentication tag that detects any tampering.")
        print("  CLI: openssl enc -aes-256-gcm -pbkdf2 -in pt.txt -out ct.bin -pass pass:P@ss")


def main() -> None:
    print("=" * 64)
    print("Cryptography Lab Demo")
    print("=" * 64)
    print()
    print("Exercises each primitive once so the guarantee is concrete.")

    demo_sha256()
    demo_aes()
    demo_rsa()
    demo_certificate()
    demo_ecb_vs_salt()
    demo_bit_flip()

    print(f"\n{'=' * 64}")
    print("Deliverable: crypto-notes.md — one line per primitive (what it")
    print("guaranteed), the ECB-vs-salted-hash side-by-side, and one verdict:")
    print("why a password must be hashed-and-salted, never encrypted.")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
