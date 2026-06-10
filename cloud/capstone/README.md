# Track 05 — Cloud & Container Security: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Cloud & Container Security
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/05-cloud/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/05-cloud).

## The capstone

Find a privilege-escalation path in a deliberately vulnerable cloud account (CloudGoat or flaws.cloud), explain it, then close it as code — Terraform gated by a scanner in CI — and detect the attack from cloud logs.

## What you build

1. An IAM/serverless privilege-escalation path walked end to end and explained.
2. The fix expressed as Terraform/IaC, gated by a scanner (Checkov/tfsec/Trivy) that fails the bad config in CI.
3. A detection from cloud logs (CloudTrail/equivalent) that catches the attack.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
cloud/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/attack-path.md            # the privesc chain, mapped to ATT&CK for Cloud
    submission/fix/                      # Terraform that closes the path
    submission/.github/ci.yml            # scanner gate that fails the bad config
    submission/detection/                # log-based detection
```

## How to use it

```bash
# from the repo root
cd cloud/capstone
# ... build your deliverable under submission/ ...
make grade          # advisory self-check against the rubric
```

`make grade` is **advisory** — this capstone is a portfolio artifact judged by a human (you,
a peer, or a reviewer) against [`rubric.md`](rubric.md), not auto-graded. Set `AI_GRADER_CMD`
to get draft LLM feedback (see `../../scripts/README.md`).

## Acceptance criteria

**Proficient is the bar to ship; exemplary is the portfolio piece.** Grade every dimension
honestly — a strong report in one column doesn't excuse a gap in another.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Attack path** | A single misconfig noted, no chain | An IAM/serverless privesc path walked end to end and explained | Multi-step chain mapped to ATT&CK for Cloud, with the trust relationship behind each hop |
| **Fix as code** | Fixed in the console (click-ops) | The fix expressed as Terraform/IaC that closes the path | Least-privilege, parameterised, reusable, with the diff proving the path is gone |
| **CI gate** | No scanner, or not enforced | A scanner runs in CI and *fails* the bad config | Tuned (no noise), blocks merge on the finding, passes on the fix |
| **Detection** | No detection, or fires on nothing | A detection from cloud logs that catches the attack | Validated against benign activity for FPs, mapped to the technique |
| **Cost & teardown** | Left billable resources running | Resources torn down; no secrets in code | Rebuilds from `terraform apply` and tears down cleanly; budget-safe |

> Use your own free-tier accounts or intentionally vulnerable environments (CloudGoat, flaws.cloud). Never test tenants you don't own; tear down billable resources when done.
