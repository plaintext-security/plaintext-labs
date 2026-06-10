# Endpoint & Host Hardening capstone — grading rubric

Self/peer/reviewer rubric for the Track 07 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Hardening coverage** | One OS, or partial baseline | Both Windows and Linux hardened to a CIS profile, as code | Tailored to a threat model — exceptions justified, not blind benchmark application |
| **Compliance scoring** | No score, or not reproducible | OpenSCAP/CIS-CAT score before and after, delta documented | Failing controls triaged (fix vs. accept-with-reason); re-run from clean state |
| **Drift detection** | None | A deliberate misconfig is introduced and the tooling flags it | Drift detection automated/scheduled; reports what changed, not just that it did |
| **Telemetry** | No telemetry, or fires on nothing | Endpoint telemetry catches a simulated attack the baseline missed | Detection mapped to ATT&CK and tuned against benign noise |
| **As-code & reproducibility** | Manual steps | A reader can re-apply the baseline from committed code | One command re-hardens a fresh host and re-scores it; idempotent |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Work on VMs/containers you own. Some hardening is destructive — snapshot first.
