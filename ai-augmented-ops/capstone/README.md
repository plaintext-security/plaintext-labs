# Track 12 — AI-Augmented Security Operations: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the AI-Augmented Security Operations
> capstone: a running stack to build on (Ollama + ChromaDB + a lab container), a stub MCP tool, a small
> seed runbook corpus (incl. a deliberately poisoned doc to red-team), plus the acceptance rubric you
> grade yourself against. The full prose, phase projects, and the rendered rubric live in the curriculum:
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
├── rubric.md          # the self-assessment rubric you grade yourself against
├── docker-compose.yml # the starter stack: Ollama + ChromaDB + lab container
├── Makefile           # make up | shell | tool | down | grade
├── tools/
│   └── incident_tool.py   # stub MCP tool (one real tool) — extend it into your copilot's tool
├── data/runbooks/     # small seed corpus, incl. 05-...-INJECTED.md (your red-team target)
└── submission/        # YOUR work goes here
    submission/copilot/                  # MCP server + RAG corpus loader
    submission/attack/                   # the prompt-injection / exfil PoC
    submission/fix/                      # the hardening + re-test showing it fails now
    submission/writeup.md                # build → attack → fix, one story
```

## How to use it

```bash
cd ai-augmented-ops/capstone
make up        # start Ollama + ChromaDB + lab; pull tinyllama + nomic-embed-text
make tool      # self-test the stub MCP tool against the seed runbooks (no client needed)
make shell     # drop into the lab container and build under submission/
make down      # tear down when finished
```

The scaffold gives you a running stack and a working one-tool MCP server so you start at the
*interesting* part. The seed corpus (`data/runbooks/`) is anchored to real incidents and includes
`05-vendor-advisory-INJECTED.md` — a deliberately poisoned runbook in the EchoLeak
(CVE-2025-32711) / Invariant Labs tool-poisoning shape. Ingest it, show your copilot follows the
hidden instruction, then harden so the same content is treated as data and the attack fails — that
build → attack → fix is the capstone.

This is an honor-system curriculum — no tool grades you. Grade yourself honestly against
[`rubric.md`](rubric.md): the capstone is a portfolio artifact judged by a human (you, a peer,
or a reviewer), and the build itself is the proof.

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
