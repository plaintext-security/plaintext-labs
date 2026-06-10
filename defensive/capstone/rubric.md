# Defensive Operations capstone — grading rubric

Self/peer/reviewer rubric for the Track 02 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Telemetry pipeline** | Logs from one source, not searchable | Host *and* network telemetry flowing into a searchable store | Reproducible as code; parsing normalised to a common schema |
| **Detection-as-code** | Rule only matches the demo data | A versioned Sigma rule mapped to ATT&CK that fires on the attack | Validated against benign data for false positives; tuning documented |
| **The catch** | Attack ran but wasn't detected | The simulated attack is caught by your detection | Catches the technique, not the exact sample — proven on a variation |
| **Investigation** | Alert noted, no follow-through | Triaged alert → root cause, supporting events cited | Full alert→containment narrative; what the attacker did and didn't |
| **Write-up & automation** | Manual, undocumented | A repeatable process and an incident write-up | An automated enrich→ticket step closes the loop; re-runs |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Use real public datasets (Malware-Traffic-Analysis.net, EVTX-ATTACK-SAMPLES) or generate the attack with Atomic Red Team against a host you own.
