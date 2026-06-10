# Zero Trust Network Access capstone — grading rubric

Self/peer/reviewer rubric for the Track 11 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **No inbound ports** | Service on an open port | Reachable only through an identity-aware proxy/tunnel; no inbound ports | Verified with an external port scan showing nothing open; egress-only tunnel proven |
| **Identity-aware access** | Single shared credential | Per-request access tied to authenticated identity (OIDC/SSO) | Device posture or hardware-bound auth (FIDO2/passkey) factored in |
| **Policy as code** | Policy clicked in a UI | Access policy as code (OPA/Rego), version-controlled | Tested — allow and deny cases asserted — and least-privilege by default |
| **Audit trail** | No logs, or logs lack identity | Access logs prove each request was authenticated and authorised | A denied-and-allowed pair shown end to end; logs feed a detection |
| **Reproducibility** | Manual, undocumented setup | A reader can stand up the proxy and policy from committed config | One command brings the gated service up; policy change is a reviewed diff |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Build with your own accounts and lab hosts. Identity-aware proxies touch real access — test against resources you own.
