# Validation — Forensics 16: Reviewing AI Incident Summaries

## Validation command

```bash
make up && make demo && make down
```

`make demo` runs `check_summary.py` over the seeded summary and bundled artifacts.
The verifier exits **1** when it finds unsupported claims — which is the EXPECTED
outcome for this seeded summary (finding the planted fabrications is the demo
passing). The `demo` target wraps that: it treats exit 1 as success (prints
`demo OK: verifier flagged the planted fabrications`) and any other code as failure.
A fail-loud error (unreadable input / unparseable summary) exits 2 and fails the demo.

## Prerequisites

- Docker + Docker Compose v2 (`docker compose`).
- ~256 MB RAM. **No network, no live model.** Image is `python:3.12-slim`; the
  verifier is **stdlib only** (no PyYAML) and runs over committed recorded fixtures.
  Fully offline and deterministic, suitable for CI.

## What gets exercised

- `data/ai-incident-summary.md` — the recorded AI-drafted summary fixture. Its YAML
  front-matter is the machine-readable claim set. **Planted fabrications (6):**
  1. `CVE-2024-3094` — well-formed but absent from evidence (hallucinated specific).
  2. `CVE-2021-44228` — well-formed but absent from evidence (hallucinated specific).
  3. `T1036.004` claimed under tactic *Persistence* — it is *Defense Evasion* (wrong tactic).
  4. dropper SHA256 `00001111…ffff` — matches no artifact (wrong hash).
  5. timeline entry `2024-03-14T23:55:00Z` "12 GB exfiltrated from S3" — no artifact (hallucinated event).
  6. **root cause** "brute-force attack cracked jchen's password" — contradicted by
     `auth.log` (a single accepted login from a new geography, no failed-password run).
     This is the one the field-checker **cannot** catch — the lesson.
- `data/artifacts/` — the primary sources: `auth.log` (syslog), `winlog_4688.csv`
  (EVTX-style process creation with the dropper's authoritative SHA256), `cloudtrail.json`
  (cloud pivot; no S3 exfil event), `pe_features.json` (Module-12 dropper record + true ATT&CK tactics).
- `scripts/check_summary.py` — extracts every CVE / ATT&CK id+tactic / hash / timeline
  timestamp and reports which trace to an artifact. Fails loud (exit 2) on unreadable/
  unparseable input; exits 1 when unsupported claims exist; exits 0 only when clean.
  Explicitly states it does **not** validate the root-cause narrative.

## Validation status (host, no Docker)

Docker is **not available in the authoring environment**, so `make up/demo/down` was
**not** run here. The verifier was validated directly on the host (it is pure stdlib,
identical to what runs in `python:3.12-slim`):

- `check_summary.py data/ai-incident-summary.md data/artifacts` →
  **flags exactly the 5 mechanical fabrications** (2 CVEs, 1 wrong tactic, 1 wrong hash,
  1 hallucinated timeline entry), **passes the 4 genuinely-supported claims**
  (the two real VPN/host timeline entries, the real C2 ATT&CK mapping, the real IAM
  event), and prints the limit note about the 6th (root-cause) fabrication. Exit code **1**.
- Fail-loud paths verified: missing summary → exit 2; missing artifacts dir → exit 2;
  summary with no front-matter → exit 2.
- The `make demo` wrapper logic (exit 1 ⇒ demo success, else fail) was simulated on the host and behaves correctly.

**Still owed before this lab counts as done:** an actual `make up && make demo &&
make down` on a clean Linux runner.

No `.ci-demo` marker is added (per task scope).
