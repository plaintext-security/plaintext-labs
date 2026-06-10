# Track 03 — Digital Forensics & Incident Response: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Digital Forensics & Incident Response
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/03-forensics/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/03-forensics).

## The capstone

Take a training disk or memory image to a root-cause incident report: acquire and verify, build a super-timeline, and reconstruct what happened — every claim tied to an artifact.

## What you build

1. A verified acquisition (hash on acquisition, verified before analysis; work on a copy).
2. A super-timeline correlating activity across at least two sources (disk + memory or + network).
3. A defensible root-cause report where every claim cites the artifact behind it.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
forensics/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/chain-of-custody.md       # hashes + handoffs
    submission/timeline/                 # super-timeline (plaso/timesketch export)
    submission/report.md                 # root cause, each claim → artifact
    submission/artifacts.md              # index of recovered artifacts (refs, not dumps)
```

## How to use it

```bash
# from the repo root
cd forensics/capstone
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
| **Evidence integrity** | No hashing, or hashes don't match | Image hashed on acquisition and verified; working on a copy; chain of custody noted | Hashes at every handoff; read-only demonstrated; order of volatility respected |
| **Artifact recovery** | Surface artifacts only | Recovered/interpreted artifacts across two+ sources | Recovered deleted/carved data or pivoted memory→disk to confirm a finding |
| **Super-timeline** | Events listed, not correlated | A timeline correlating activity across sources, key events called out | Pivots reconstruct the full sequence; gaps and anti-forensics noted |
| **Root-cause verdict** | Conclusion unsupported | A defensible root cause; every claim cites its artifact | Initial access → actions → impact, with confidence levels and what's not proven |
| **Reporting** | Notes, not a report | Clear narrative an investigator could reproduce | Survives scrutiny: methodology, tooling, hashes, limitations all documented |

> Use public training images (memory dumps, disk images) and never examine evidence you are not authorised to handle.
