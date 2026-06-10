# Track 11 — Zero Trust Network Access: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Zero Trust Network Access
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/11-ztna/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/11-ztna).

## The capstone

Publish a lab service with no inbound ports behind an identity-aware proxy (Pomerium or Cloudflare Tunnel + Access), enforce an access policy as code with OPA, and show the access logs that prove every request was authenticated and authorised.

## What you build

1. A lab service reachable only through an identity-aware proxy/tunnel — no inbound ports.
2. An access policy expressed as code (OPA/Rego), version-controlled and tested (allow *and* deny cases).
3. An audit trail showing a denied-and-allowed request pair end to end.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
ztna/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/proxy/                    # Pomerium / Cloudflare Tunnel config
    submission/policy/                   # OPA/Rego, with allow + deny tests
    submission/audit/                    # access-log excerpts (identity present)
    submission/portscan.md               # proof nothing is listening inbound
```

## How to use it

```bash
# from the repo root
cd ztna/capstone
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
| **No inbound ports** | Service on an open port | Reachable only through an identity-aware proxy/tunnel; no inbound ports | Verified with an external port scan showing nothing open; egress-only tunnel proven |
| **Identity-aware access** | Single shared credential | Per-request access tied to authenticated identity (OIDC/SSO) | Device posture or hardware-bound auth (FIDO2/passkey) factored in |
| **Policy as code** | Policy clicked in a UI | Access policy as code (OPA/Rego), version-controlled | Tested — allow and deny cases asserted — and least-privilege by default |
| **Audit trail** | No logs, or logs lack identity | Access logs prove each request was authenticated and authorised | A denied-and-allowed pair shown end to end; logs feed a detection |
| **Reproducibility** | Manual, undocumented setup | A reader can stand up the proxy and policy from committed config | One command brings the gated service up; policy change is a reviewed diff |

> Build with your own accounts and lab hosts. Identity-aware proxies touch real access — test against resources you own.
