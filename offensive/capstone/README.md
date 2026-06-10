# Track 01 — Offensive Security: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Offensive Security
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/01-offensive/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/01-offensive).

## The capstone

Run a full engagement against an intentionally vulnerable target — recon through exploitation, privilege escalation, and lateral movement — and deliver a professional report a defender can act on. The report is the artifact, not the shell.

## What you build

1. A scoped engagement against an authorised, intentionally vulnerable target (Vulhub CVE, a local VM, or a free CTF range).
2. An attack chain documented as phases: recon → exploit → privesc → lateral movement, each mapped to MITRE ATT&CK.
3. A professional report: exec summary, severity-ranked findings with reproducible evidence, business impact, and prioritised remediation.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
offensive/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/report.md                 # the deliverable — exec summary + findings
    submission/findings/                 # one file per finding: repro steps + evidence ref
    submission/attack-chain.md           # the phased timeline, mapped to ATT&CK
    submission/scope.md                  # authorised scope + rules of engagement
```

## How to use it

```bash
# from the repo root
cd offensive/capstone
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
| **Methodology & scope** | Ad-hoc; no phases; scope unstated | Recon → exploit → privesc → lateral movement documented as phases, all in stated scope | Maps each action to ATT&CK and PTES, with timestamps forming an attack timeline |
| **Findings quality** | Asserted without proof, or scanner-copied | Each finding has CVE/CWE, reproducible steps, evidence, validated by hand | Every finding rated by real business impact, with a replayable PoC |
| **Exploitation** | One-click exploit not understood | Gained access and escalated; can explain why each exploit worked | Chained foothold → DA/root, noting detection opportunities at each step |
| **Remediation** | Generic advice | Specific, prioritised fix per finding | Fixes are testable and mapped to root cause, not symptom |
| **Report craft** | Disorganised; not actionable | Clear exec summary + technical detail; reproducible | Professional deliverable: severity-ranked, evidence-linked, ticketable |
| **Authorization & safety** | Out-of-scope actions, or no scope note | Every action provably in scope; authorization stated | Demonstrates restraint — destructive steps avoided or explicitly authorised |

> **Authorization is mandatory.** Only test systems you own or have explicit written permission to test. Point these techniques only at intentionally vulnerable targets.
