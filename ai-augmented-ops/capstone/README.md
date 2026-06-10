# Track 12 — AI-Augmented Security Operations: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the AI-Augmented Security Operations
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/12-ai-augmented-ops/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/12-ai-augmented-ops).

## The capstone

Build a small SoC copilot — an MCP server exposing one real tool, grounded in a RAG corpus of your own notes — then red-team it: demonstrate a prompt-injection or data-exfil weakness and harden against it.

## What you build

1. A SoC copilot: an MCP server exposing one real tool, grounded in a RAG corpus of your own notes.
2. A working prompt-injection or data-exfil exploit demonstrated against your own copilot, mapped to OWASP LLM Top 10 / MITRE ATLAS.
3. A concrete hardening that defeats the demonstrated attack, re-tested so the same attack now fails.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
ai-augmented-ops/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/copilot/                  # MCP server + RAG corpus loader
    submission/attack/                   # the prompt-injection / exfil PoC
    submission/fix/                      # the hardening + re-test showing it fails now
    submission/writeup.md                # build → attack → fix, one story
```

## How to use it

```bash
# from the repo root
cd ai-augmented-ops/capstone
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
| **The copilot** | Bare LLM call, no grounding/tools | MCP server exposing one real tool, grounded in a RAG corpus of your notes | Genuinely useful for a SOC task; retrieval relevant and tools scoped |
| **The attack** | Theoretical, not demonstrated | A working prompt-injection or data-exfil exploit shown against your own system | Mapped to OWASP LLM Top 10 / MITRE ATLAS; shows real impact |
| **The fix** | Generic advice, not applied | A concrete hardening that defeats the demonstrated attack | Re-tested: same attack now fails; defence-in-depth (input + tool-scoping + output) |
| **Tool & data scoping** | Tools/access unbounded | Tools and retrieval scoped to least privilege | Untrusted content can't reach privileged tools; trust boundary explicit |
| **Write-up** | Disconnected pieces | Build → attack → fix told as one coherent story | Honest about residual risk and what the model can still be tricked into |

> Test prompt-injection and jailbreak techniques only against models and applications you own or are authorised to assess.
