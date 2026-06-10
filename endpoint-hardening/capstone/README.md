# Track 07 — Endpoint & Host Hardening: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Endpoint & Host Hardening
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/07-endpoint-hardening/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/07-endpoint-hardening).

## The capstone

Harden a Windows and a Linux host to CIS as code, score the before/after compliance, prove drift detection catches a deliberate misconfiguration, and show telemetry firing on a simulated attack.

## What you build

1. Both a Windows and a Linux host hardened to a CIS profile, expressed as code (Ansible/GPO/SCAP).
2. Before/after compliance scores (OpenSCAP/CIS-CAT) with the delta, and drift detection that flags a deliberate misconfiguration.
3. Endpoint telemetry that catches a simulated attack the baseline didn't stop, mapped to ATT&CK.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
endpoint-hardening/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/hardening/                # Ansible/GPO/SCAP, both OSes
    submission/scores.md                 # before/after compliance delta
    submission/drift/                    # the planted misconfig + the alert it raised
    submission/telemetry/                # detection of the simulated attack
```

## How to use it

```bash
# from the repo root
cd endpoint-hardening/capstone
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
| **Hardening coverage** | One OS, or partial baseline | Both Windows and Linux hardened to a CIS profile, as code | Tailored to a threat model — exceptions justified, not blind benchmark application |
| **Compliance scoring** | No score, or not reproducible | OpenSCAP/CIS-CAT score before and after, delta documented | Failing controls triaged (fix vs. accept-with-reason); re-run from clean state |
| **Drift detection** | None | A deliberate misconfig is introduced and the tooling flags it | Drift detection automated/scheduled; reports what changed, not just that it did |
| **Telemetry** | No telemetry, or fires on nothing | Endpoint telemetry catches a simulated attack the baseline missed | Detection mapped to ATT&CK and tuned against benign noise |
| **As-code & reproducibility** | Manual steps | A reader can re-apply the baseline from committed code | One command re-hardens a fresh host and re-scores it; idempotent |

> Work on VMs/containers you own. Some hardening is destructive — snapshot first.
