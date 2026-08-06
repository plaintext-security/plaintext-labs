# ZTNA Track — Coverage Expansion Plan (ledger)

Closes the enterprise-coverage gaps from the 2026-08-06 review. Two repos:
- **plaintext** (`/Users/patrick/Development/plaintext`): `tracks/11-ztna/modules/<M>/README.md` + `cheatsheet.md` + `lab.md` (symlink → labs); `mkdocs.yml` nav; track README.
- **plaintext-labs** (`/Users/patrick/Development/plaintext/plaintext-labs`, submodule of plaintext): `ztna/<M>/lab.md` + artifacts; `ztna/capstone/`.

Symlink pattern: `tracks/11-ztna/modules/<M>/lab.md -> ../../../../plaintext-labs/ztna/<M>/lab.md`.

## Decisions

- **Numbering: append, don't insert** (modules cross-reference by number heavily).
  - Rename `10-workload-identity-mtls` → `12-workload-identity-mtls` (dir in BOTH repos, symlink, mkdocs nav, track README, its lab title already says "Lab 12").
  - New: `13-privileged-access`, `14-data-pillar`.
- **Tools:** M13 = Teleport Community Edition (Docker). M14 = reuse OPA (M08) + Sigma (M09) + assessed-from-config CASB/DLP.
- Lab format = the hands-on cognitive-load template (see `ztna/12-workload-identity-mtls/lab.md` and `ztna/02-identity-control-plane/lab.md`). README/cheatsheet format = `tracks/11-ztna/modules/02-identity-control-plane/{README,cheatsheet}.md`.

## Workstreams

### A. Housekeeping — rename workload-identity 10 → 12 (controller)
- `git mv` `ztna/10-workload-identity-mtls` → `ztna/12-workload-identity-mtls` (plaintext-labs).
- `git mv` `tracks/11-ztna/modules/10-workload-identity-mtls` → `12-...` (plaintext); re-point its `lab.md` symlink.
- mkdocs nav: update the 3 workload lines.
- track README: table row + any prose.

### B. New Module 13 — Privileged Access (subagent)
Files — plaintext-labs `ztna/13-privileged-access/`: `lab.md`, `Makefile`, `docker-compose.yml`, Teleport config, `check-access.sh`. plaintext `tracks/11-ztna/modules/13-privileged-access/`: `README.md`, `cheatsheet.md`.
- Thesis: user→app ZTNA is table stakes; the enterprise fight is admin access to infra (SSH/RDP/DB/kubectl). Replace standing keys + shared bastion with short-lived identity-bound certs, per-session authz, recorded sessions — privileged access is SPIFFE-for-humans.
- Tool: Teleport CE. Lab proves: authorized user gets a short-lived cert + recorded SSH session via the proxy; unauthorized role / expired cert / direct-to-node bypass all denied; tighten an RBAC role (least privilege).
- Cite: MITRE T1021 (Remote Services), T1078 (Valid Accounts); Uber 2022 (contractor creds → hardcoded admin creds → privileged sprawl); NIST 800-207 (PEP for admin), CISA ZTMM Identity pillar; JIT access / session recording / break-glass.
- Connects: back to M02 (identity) + M12 (SPIFFE = machine analog); forward to capstone (audit trail).

### C. New Module 14 — Data, the Last Pillar (subagent)
Files — plaintext-labs `ztna/14-data-pillar/`: `lab.md`, `Makefile`, `docker-compose.yml`, Rego policy, labeled corpus, Sigma rule, `check-data.sh`. plaintext `tracks/11-ztna/modules/14-data-pillar/`: `README.md`, `cheatsheet.md`.
- Thesis: ZT isn't done when the request is authorized — data is the 5th NIST pillar. A correctly-authenticated user still must not exfiltrate restricted data. Label data, drive label-based authz (OPA), detect exfil-shaped access (Sigma), understand CASB/DLP.
- Tools: reuse OPA (M08) + Sigma (M09). Lab proves: authz by (role × classification) denies a restricted read by a non-privileged authenticated user; unlabeled → treated restricted (fail-closed); a Sigma rule fires on bulk/anomalous restricted reads, silent on normal; CASB/DLP/encryption mapped assessed-from-config.
- Cite: NIST 800-207 + CISA ZTMM Data pillar; Snowflake 2024 mass-exfil (stolen creds, no MFA, no data-layer guardrails); MITRE T1567 (Exfil Over Web Service), T1530 (Data from Cloud Storage).
- Connects: reuses M08 + M09; completes the 5 pillars; forward to capstone.

### D. Edits (controller)
- **M05** README + lab: frame the Cloudflare Access lab as third-party/BYOD clientless access — a time-boxed external-auditor scenario, prove what they can't reach.
- **M07** README: add the missing NIST/CISA anchor (Networks pillar) — one line, matching the other modules' framework citations.
- **M10-vpn-ztna-migration** lab.md: add a legacy-app cohort — one that gets header-injection SSO at the proxy (M06 machinery), one that stays on a shrinking mesh segment (M03/M07).
- **Capstone** rubric (`ztna/capstone/rubric.md`): add Exemplary-tier rows pulling in M07 (east-west policy proven), M09 (a built detection firing on the capstone's own logs), M11 (attack harness re-run green), M12 (workload mTLS).
- **Track README**: add M13/M14 to the module table + phase narrative; add the boundary-seam note ("perimeter/egress controls live in the [boundary] track; this track begins where the perimeter ends").
- **M02 or M09** README: a CAEP / continuous-evaluation paragraph (revocation/step-up/session-kill between issuance and expiry).
- **mkdocs nav**: add M13/M14 (Concept/Lab/Cheat sheet) + workload rename.

### E. Land it (controller)
- plaintext-labs: commit + push main; replicate to HERE (`-patrickdaj`).
- plaintext: symlinks + nav + README edits + bump submodule; commit + push main.
- Deploy: dispatch `deploy-pages.yml` (push auto-trigger still flaky); verify new module pages live.

## Ledger
- [ ] A rename  · [ ] B M13  · [ ] C M14  · [ ] D edits  · [ ] E land+deploy
