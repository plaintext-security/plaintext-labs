# Security Automation capstone — grading rubric

Self/peer/reviewer rubric for the Track 10 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **CI gate** | Scanner runs but doesn't block | A misconfig is *blocked before deploy* by a scanner in CI | Tuned (no FP noise), passes the fixed config, explains the failure |
| **SOAR playbook** | Linear automation, no human gate | Enrich → contain → ticket with an explicit human approval step | Idempotent, handles failure/rollback, logs each action for audit |
| **As-code discipline** | Click-ops or untracked scripts | Pipeline and playbook are version-controlled, reviewable code | Modular and reusable across labs; secrets handled out of band |
| **Review of AI output** | Generated YAML/HCL shipped unread | The note names what AI generated and what you corrected | A concrete over-broad-RBAC / wildcard-IAM / missing-gate catch documented and fixed |
| **Reproducibility** | Runs only on your machine | A reader can run the pipeline and trigger the playbook | One command stands up the whole loop; teardown is clean |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Run automation against your own accounts and lab infrastructure only. Generated IaC can create real, billable resources — review before you apply.
