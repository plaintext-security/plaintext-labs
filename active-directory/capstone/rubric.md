# Active Directory & Windows Security capstone — grading rubric

Self/peer/reviewer rubric for the Track 06 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Attack path** | One technique in isolation | Low-priv → DA path walked, each hop validated in the lab | BloodHound path confirmed by hand, alternatives noted, each step mapped to ATT&CK |
| **Hardening as code** | Manual GPO clicks | Each abused step closed via reviewed config-as-code | Tiering/least-privilege applied; changes idempotent and re-runnable |
| **Posture measurement** | No before/after | PingCastle score before and after, with the delta | Delta tied to specific paths closed; residual risk acknowledged |
| **Detections** | No detection for steps used | A detection per step used, tested to fire on lab activity | Honeytoken or behaviour-based detection beyond signatures; FP-tested |
| **Write-up** | Screenshots without narrative | Clear before/after story a blue and red reader can follow | Reproducible: lab build, attack, fix, detection all documented |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Build your own lab domain (GOAD, or a local Windows eval VM). Only attack environments you own. This capstone needs Windows VMs — it runs locally, not in hosted Codespaces.
