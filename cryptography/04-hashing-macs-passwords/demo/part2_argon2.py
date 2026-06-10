"""Part 2: Argon2id password hashing — the correct, deliberately-slow approach."""
import time
from argon2 import PasswordHasher

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
passwords = ["password123", "meridian2024", "Tr0ub4dor&3"]

print("Argon2id hashing (each takes ~100-300ms):")
for pwd in passwords:
    start = time.perf_counter()
    h = ph.hash(pwd)
    elapsed = time.perf_counter() - start
    print(f"  Hashed in {elapsed:.3f}s: {h[:50]}...")
print()
print("At 3ms per hash: attacker can try ~333 hashes/sec")
print("vs SHA-256 (ns/hash): Argon2id is ~millions of times slower to brute-force")
