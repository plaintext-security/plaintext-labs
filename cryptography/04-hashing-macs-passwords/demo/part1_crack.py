"""Part 1: SHA-256 hash cracking simulation against a wordlist."""
import hashlib

# Build lookup table from wordlist
db = {}
with open("data/passwords.txt") as f:
    for line in f:
        pwd = line.strip()
        if pwd:
            db[hashlib.sha256(pwd.encode()).hexdigest()] = pwd

# Simulate hashes from a breached database
targets = {
    hashlib.sha256(b"password123").hexdigest(): "target-1",
    hashlib.sha256(b"meridian2024").hexdigest(): "target-2",
    hashlib.sha256(b"Tr0ub4dor&3").hexdigest(): "target-3",
}

print("Cracking unsalted SHA-256 hashes:")
cracked = 0
for h, label in targets.items():
    result = db.get(h, None)
    if result:
        print(f"  CRACKED [{label}]: {h[:16]}... => {result}")
        cracked += 1
    else:
        print(f"  NOT FOUND [{label}]: {h[:16]}...")
print(f"Result: {cracked}/{len(targets)} cracked from wordlist")
