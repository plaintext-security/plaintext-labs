# Digital Forensics & Incident Response capstone — grading rubric

Self/peer/reviewer rubric for the Track 03 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Evidence integrity** | No hashing, or hashes don't match | Image hashed on acquisition and verified; working on a copy; chain of custody noted | Hashes at every handoff; read-only demonstrated; order of volatility respected |
| **Artifact recovery** | Surface artifacts only | Recovered/interpreted artifacts across two+ sources | Recovered deleted/carved data or pivoted memory→disk to confirm a finding |
| **Super-timeline** | Events listed, not correlated | A timeline correlating activity across sources, key events called out | Pivots reconstruct the full sequence; gaps and anti-forensics noted |
| **Root-cause verdict** | Conclusion unsupported | A defensible root cause; every claim cites its artifact | Initial access → actions → impact, with confidence levels and what's not proven |
| **Reporting** | Notes, not a report | Clear narrative an investigator could reproduce | Survives scrutiny: methodology, tooling, hashes, limitations all documented |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Use public training images (memory dumps, disk images) and never examine evidence you are not authorised to handle.
