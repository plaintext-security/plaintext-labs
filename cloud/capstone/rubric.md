# Cloud & Container Security capstone — grading rubric

Self/peer/reviewer rubric for the Track 05 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Attack path** | A single misconfig noted, no chain | An IAM/serverless privesc path walked end to end and explained | Multi-step chain mapped to ATT&CK for Cloud, with the trust relationship behind each hop |
| **Fix as code** | Fixed in the console (click-ops) | The fix expressed as Terraform/IaC that closes the path | Least-privilege, parameterised, reusable, with the diff proving the path is gone |
| **CI gate** | No scanner, or not enforced | A scanner runs in CI and *fails* the bad config | Tuned (no noise), blocks merge on the finding, passes on the fix |
| **Detection** | No detection, or fires on nothing | A detection from cloud logs that catches the attack | Validated against benign activity for FPs, mapped to the technique |
| **Cost & teardown** | Left billable resources running | Resources torn down; no secrets in code | Rebuilds from `terraform apply` and tears down cleanly; budget-safe |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Use your own free-tier accounts or intentionally vulnerable environments (CloudGoat, flaws.cloud). Never test tenants you don't own; tear down billable resources when done.
