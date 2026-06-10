# Lab 09 — Crack Real Password Hashes

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/09-password-attacks
make up
```

The lab container has Python + passlib + bcrypt; no GPU required. The bundled
`data/hashes.txt` contains 11 hashes from a simulated Meridian Financial dump
(MD5, NTLM, bcrypt, SHA-256, SHA-1) — passwords drawn from rockyou.txt.

## Scenario

You've exfiltrated a credential dump from Meridian Financial's internal
identity store. Crack it the way an attacker would: identify hash types,
run a dictionary attack, apply rules-based mutations, then assess what
defenses would have stopped you.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Before cracking anything, identify each hash type in `data/hashes.txt` by
   inspection. (How do you tell NTLM from MD5 by length/format alone? Why does a bcrypt
   hash start with `$2b$12$…`? What does the `aad3b435…` NTLM value tell you without
   cracking it?) You'll choose the right algorithm/mode per type from this.

2. [ ] Run a dictionary attack against the dump yourself and crack what falls fast. (Point
   a real cracker at the hashes with a wordlist drawn from rockyou.txt — which tool and
   mode per hash type?) Note which hashes fell in milliseconds and which stood.

3. [ ] Trace the dictionary attack in `crack.py` and follow the flow:
   `load_hashes()` → `crack_hash()` → `ntlm()`/`md5()` → compare. (`make demo` runs the
   full validated pipeline — use it to check your results against the reference run.)

4. [ ] Explain why most hashes cracked in milliseconds but bcrypt did not. Review the KDF
   comparison output — what is the cost factor doing?

5. [ ] Re-run with rule-based mutations enabled and observe which additional hashes (if
   any) fall. What mutations does `apply_rules()` try, and why are they realistic?

6. [ ] Write the three defenses you'd recommend Meridian adopt, ranked by impact.

## Success criteria — you're done when

- [ ] You can identify hash types from format alone (bcrypt vs NTLM vs SHA-256).
- [ ] You understand *why* MD5/SHA-1 are broken for passwords (speed, not just length).
- [ ] You cracked ≥8/11 hashes and can explain the ones that resisted.
- [ ] You can state the defenses (slow KDF ≥ cost 12, salt, length ≥ 15, MFA) that defeat offline cracking.

## Deliverables

`cracking.md`: hash types identified, which cracked (mode + time), and the three
defenses you'd prioritise for Meridian. (Don't commit real wordlists or raw dumps.)

## Automate & own it

**Required.** Extend `crack.py` or write a new `auto_crack.py` that:
- Reads a hash file
- Auto-identifies hash types
- Selects the right algorithm
- Outputs a Markdown report with crack results + recommended mitigations

AI drafts the script; you review every function before committing. Commit
`auto_crack.py` and your `cracking.md` alongside it.

## AI acceleration

Ask a model to identify a hash from its format and suggest the hashcat mode —
then verify before you spend GPU time. A wrong mode is hours wasted.
Also: prompt a model to generate a contextual wordlist for "Meridian Financial"
(company names, financial jargon) and check what it adds to the hit rate.

## Connects forward

Cracked credentials feed lateral movement (module 12). In the Active Directory
track, Kerberoasting hands you crackable service-ticket hashes the same way —
same cracking pipeline, same KDF weakness, just a different dump vector.

## Marketable proof

> "I crack real password hashes — identifying types, choosing attack modes, applying
> rules-based mutations — and can argue the hashing and MFA defenses that defeat it."

## Stretch

- Crack a captured NTLMv2 hash (Responder output) — note how `Net-NTLMv2`
  differs from an NTLM database dump.
- Benchmark the full rockyou.txt against MD5 (extrapolate from the KDF comparison)
  and argue when a GPU cluster changes the calculus.
