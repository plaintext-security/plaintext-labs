"""Part 1: GCM IV reuse attack — reusing a nonce leaks the XOR of plaintexts."""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = os.urandom(32)
BAD_IV = b"\x00" * 12  # hardcoded IV — the bug

msg1 = b"Salary: $95,000 "
msg2 = b"Budget: $200,000"

ct1 = AESGCM(key).encrypt(BAD_IV, msg1, None)
ct2 = AESGCM(key).encrypt(BAD_IV, msg2, None)

# XOR the ciphertexts (first 16 bytes = ciphertext, last 16 = tag)
xor_ct = bytes(a ^ b for a, b in zip(ct1[:16], ct2[:16]))
xor_pt = bytes(a ^ b for a, b in zip(msg1, msg2))

print("IV reuse attack:")
print(f"  XOR of ciphertexts: {xor_ct.hex()}")
print(f"  XOR of plaintexts:  {xor_pt.hex()}")
print(f"  Match: {xor_ct == xor_pt}")
print()
print("An attacker who knows msg1 can recover msg2 by XOR-ing with ct1 XOR ct2.")
