# Track 10 — Security Automation: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Security Automation
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/10-automation/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/10-automation).

## The capstone

Build a pipeline that gates a misconfiguration before deploy *and* a SOAR playbook that responds to an alert with a human approval step — both as reviewed, version-controlled code.

## What you build

1. A CI pipeline that blocks a misconfiguration before deploy via a scanner gate.
2. A SOAR playbook: enrich → contain → ticket with an explicit human approval step.
3. A note naming what AI generated and what you corrected (an over-broad RBAC / wildcard IAM / missing-gate catch).

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
automation/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/pipeline/.github/ci.yml   # the scanner gate
    submission/pipeline/bad-config/      # the config the gate must block
    submission/playbook/                 # enrich → contain → ticket (Shuffle/n8n export)
    submission/ai-review.md              # AI-generated vs. corrected
```

## How to use it

```bash
# from the repo root
cd automation/capstone
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
| **CI gate** | Scanner runs but doesn't block | A misconfig is *blocked before deploy* by a scanner in CI | Tuned (no FP noise), passes the fixed config, explains the failure |
| **SOAR playbook** | Linear automation, no human gate | Enrich → contain → ticket with an explicit human approval step | Idempotent, handles failure/rollback, logs each action for audit |
| **As-code discipline** | Click-ops or untracked scripts | Pipeline and playbook are version-controlled, reviewable code | Modular and reusable across labs; secrets handled out of band |
| **Review of AI output** | Generated YAML/HCL shipped unread | The note names what AI generated and what you corrected | A concrete over-broad-RBAC / wildcard-IAM / missing-gate catch documented and fixed |
| **Reproducibility** | Runs only on your machine | A reader can run the pipeline and trigger the playbook | One command stands up the whole loop; teardown is clean |

> Run automation against your own accounts and lab infrastructure only. Generated IaC can create real, billable resources — review before you apply.
