"""Part 2: correct AES-GCM usage — a fresh random IV per encryption."""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = os.urandom(32)
msg = b"Salary: $95,000 for Q3 payroll"

# Two encryptions of the same message — IVs MUST differ
iv1 = os.urandom(12)
iv2 = os.urandom(12)

ct1 = AESGCM(key).encrypt(iv1, msg, None)
ct2 = AESGCM(key).encrypt(iv2, msg, None)

print("Correct (random IV per encryption):")
print(f"  Encryption 1 IV: {iv1.hex()}")
print(f"  Encryption 2 IV: {iv2.hex()}")
print(f"  IVs differ: {iv1 != iv2}")
print(f"  Ciphertexts differ: {ct1[:16].hex() != ct2[:16].hex()}")
print()
print("No IV reuse — XOR attack fails.")
