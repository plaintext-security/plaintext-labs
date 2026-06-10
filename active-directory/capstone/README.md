# Track 06 — Active Directory & Windows Security: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Active Directory & Windows Security
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/06-active-directory/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/06-active-directory).

## The capstone

Find an attack path from a low-privilege user to Domain Admin in a lab domain, walk it, then close it: harden as code and write detections for each step you used.

## What you build

1. A low-priv → Domain Admin path walked in a lab domain (GOAD or a local Windows eval domain), each hop validated.
2. Each abused step closed via reviewed config-as-code (GPO/PowerShell/Ansible), with a before/after posture score.
3. A detection per attack step, tested to fire on the lab activity.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
active-directory/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/attack-path.md            # low-priv → DA, each hop mapped to ATT&CK
    submission/hardening/                # config-as-code closing each step
    submission/posture-score.md          # PingCastle before/after delta
    submission/detections/               # one detection per attack step
```

## How to use it

```bash
# from the repo root
cd active-directory/capstone
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
| **Attack path** | One technique in isolation | Low-priv → DA path walked, each hop validated in the lab | BloodHound path confirmed by hand, alternatives noted, each step mapped to ATT&CK |
| **Hardening as code** | Manual GPO clicks | Each abused step closed via reviewed config-as-code | Tiering/least-privilege applied; changes idempotent and re-runnable |
| **Posture measurement** | No before/after | PingCastle score before and after, with the delta | Delta tied to specific paths closed; residual risk acknowledged |
| **Detections** | No detection for steps used | A detection per step used, tested to fire on lab activity | Honeytoken or behaviour-based detection beyond signatures; FP-tested |
| **Write-up** | Screenshots without narrative | Clear before/after story a blue and red reader can follow | Reproducible: lab build, attack, fix, detection all documented |

> Build your own lab domain (GOAD, or a local Windows eval VM). Only attack environments you own. This capstone needs Windows VMs — it runs locally, not in hosted Codespaces.
