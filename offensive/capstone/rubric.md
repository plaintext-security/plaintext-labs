# Offensive Security capstone — grading rubric

Self/peer/reviewer rubric for the Track 01 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Methodology & scope** | Ad-hoc; no phases; scope unstated | Recon → exploit → privesc → lateral movement documented as phases, all in stated scope | Maps each action to ATT&CK and PTES, with timestamps forming an attack timeline |
| **Findings quality** | Asserted without proof, or scanner-copied | Each finding has CVE/CWE, reproducible steps, evidence, validated by hand | Every finding rated by real business impact, with a replayable PoC |
| **Exploitation** | One-click exploit not understood | Gained access and escalated; can explain why each exploit worked | Chained foothold → DA/root, noting detection opportunities at each step |
| **Remediation** | Generic advice | Specific, prioritised fix per finding | Fixes are testable and mapped to root cause, not symptom |
| **Report craft** | Disorganised; not actionable | Clear exec summary + technical detail; reproducible | Professional deliverable: severity-ranked, evidence-linked, ticketable |
| **Authorization & safety** | Out-of-scope actions, or no scope note | Every action provably in scope; authorization stated | Demonstrates restraint — destructive steps avoided or explicitly authorised |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] **Authorization is mandatory.** Only test systems you own or have explicit written permission to test. Point these techniques only at intentionally vulnerable targets.
