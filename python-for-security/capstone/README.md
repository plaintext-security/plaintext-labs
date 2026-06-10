# Track 09 — Python for Security: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Python for Security
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/09-python-for-security/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/09-python-for-security).

## The capstone

Build a small but genuinely useful security tool — e.g. an IOC enrichment CLI or an MCP server that exposes a tool to an LLM — with tests and a README, then write up what AI wrote and what you changed.

## What you build

1. A genuinely useful security tool (enrichment CLI, parser, or MCP tool) with a real `--help` and graceful error handling.
2. A `pytest` suite covering core logic and malformed/edge input, runnable in CI.
3. A write-up naming what AI generated, what you changed, and a bug/risk you caught in the generated code.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
python-for-security/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/src/                      # the tool (packaged, importable)
    submission/tests/                    # pytest, incl. failure modes
    submission/README.md                 # what it does + how to run
    submission/ai-review.md              # what AI wrote vs. what you changed
```

## How to use it

```bash
# from the repo root
cd python-for-security/capstone
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
| **Usefulness** | A toy re-implementing a one-liner | Solves a real security task you'd actually reach for | Fills a real gap; handles a workflow start to finish |
| **Code quality** | Monolithic; no error handling | Structured, handles malformed input, passes `ruff`, has `--help` | Idiomatic, typed, packaged installable; clean separation of concerns |
| **Tests** | None, or happy-path only | `pytest` covering core logic *and* edge/malformed input | Meaningful coverage incl. failure modes; tests run in CI |
| **Robustness** | Crashes on bad input/API errors | Fails gracefully; rate-limits/retries on API calls | Secrets handled safely (env, not hardcoded); validates input |
| **Ownership of AI code** | Pasted AI output unread | Write-up names what AI generated and what you changed and why | Documents a caught bug/risk in the generated code that you fixed |

> No live target needed; if the tool talks to an API, use your own keys (env vars, never committed).
