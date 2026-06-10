# Track 00 — Foundations: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Foundations
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/00-foundations/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/00-foundations).

## The capstone

Prove core security literacy in one committed artifact: capture and walk an HTTP exchange end to end (DNS → TCP handshake → TLS), decode a layered encoded blob, and threat-model the small system you stood up.

## What you build

1. A capture write-up walking DNS → TCP three-way handshake → TLS ClientHello, each identified by packet number and explained in your own words.
2. A layered encoded blob decoded to plaintext by a committed script (not just CyberChef clicks), with each encoding named in order.
3. A one-page STRIDE model of your lab, mapping trust boundaries to threats and mitigations.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
foundations/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/capture-walkthrough.md   # DNS/TCP/TLS, by packet number
    submission/decode.py                 # peels the layered blob to plaintext
    submission/threat-model.md           # one-page STRIDE
    submission/README.md                 # how to reproduce all three
```

## How to use it

```bash
# from the repo root
cd foundations/capstone
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
| **Packet-capture walk-through** | Capture exists but layers aren't separated; DNS/TCP/TLS conflated | DNS lookup, the three-way handshake, and the TLS hello each identified by packet number and explained in your own words | Adds the *why* — SNI, encrypted vs. cleartext after ClientHello, one security-relevant header — tied to the relevant RFC |
| **Decoding the blob** | One layer peeled; tool used as a black box | All layers decoded to plaintext, with the order and each encoding (base64/hex/URL) named | Decoded by a committed script, with a note on how you recognised each layer |
| **STRIDE model** | Lists assets only, or generic threats | One page mapping trust boundaries to STRIDE with a concrete threat per relevant category | Threats ranked, each with a mitigation, referencing components you built |
| **Secret & git hygiene** | Artifacts (`.pcap`, keys) committed, or history dirty | No captures/keys/secrets in history; `.gitignore` present; clean commits | Pre-commit secret scan wired in; commits tell the build story |
| **Reproducibility** | Steps not written down | A reader can follow your write-up and reproduce each result | One `make`/script rebuilds the lab and re-runs the decode from zero |

> No live target is attacked here; you capture your own traffic to a host you control.
