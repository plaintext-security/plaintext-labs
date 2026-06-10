# Track 02 — Defensive Operations: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Defensive Operations
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/02-defensive/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/02-defensive).

## The capstone

Stand up a telemetry pipeline, simulate an attack (Atomic Red Team or a replayed PCAP), and catch it: ship the logs, write detection-as-code mapped to ATT&CK, and produce an incident write-up from alert to root cause.

## What you build

1. A telemetry pipeline ingesting host *and* network data into a searchable store.
2. A versioned Sigma detection mapped to ATT&CK that fires on the simulated attack and stays quiet on benign data.
3. An incident write-up from alert to root cause, with an automated enrich → ticket step closing the loop.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
defensive/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/pipeline/                 # pipeline config (as code)
    submission/detections/               # Sigma rules, mapped to ATT&CK
    submission/incident-report.md        # alert → root cause
    submission/automation/               # the enrich → ticket step
```

## How to use it

```bash
# from the repo root
cd defensive/capstone
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
| **Telemetry pipeline** | Logs from one source, not searchable | Host *and* network telemetry flowing into a searchable store | Reproducible as code; parsing normalised to a common schema |
| **Detection-as-code** | Rule only matches the demo data | A versioned Sigma rule mapped to ATT&CK that fires on the attack | Validated against benign data for false positives; tuning documented |
| **The catch** | Attack ran but wasn't detected | The simulated attack is caught by your detection | Catches the technique, not the exact sample — proven on a variation |
| **Investigation** | Alert noted, no follow-through | Triaged alert → root cause, supporting events cited | Full alert→containment narrative; what the attacker did and didn't |
| **Write-up & automation** | Manual, undocumented | A repeatable process and an incident write-up | An automated enrich→ticket step closes the loop; re-runs |

> Use real public datasets (Malware-Traffic-Analysis.net, EVTX-ATTACK-SAMPLES) or generate the attack with Atomic Red Team against a host you own.
