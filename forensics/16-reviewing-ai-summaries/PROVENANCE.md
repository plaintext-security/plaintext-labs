# Data provenance — Lab 16 (Reviewing AI Incident Summaries)

## Committed fixtures (zero-cost default)

The review runs **offline and deterministically** against a recorded, committed AI summary and the
primary artifacts it claims to describe — no live model, no network:

- `data/ai-incident-summary.md` — a *recorded* AI-generated summary (front-matter is the
  machine-readable claim set the verifier parses). It carries **deliberately planted fabrications**:
  well-formed-but-nonexistent CVEs, an ATT&CK technique under the wrong tactic, a wrong hash, an
  unsupported S3-exfil timeline entry, and a brute-force root cause the evidence contradicts.
- `data/artifacts/` — the primary artifacts the claims must trace to:
  - `auth.log` — VPN/SSH gateway extract; shows a single clean accepted login (not a brute-force burst).
  - `winlog_4688.csv` — Security 4688 process-creation extract from `BEACHHEAD-WS01`; carries the
    authoritative `svchost32.exe` SHA-256.
  - `cloudtrail.json` — CloudTrail slice (`jsmith` federated session, `prod-deploy` role); contains
    **no** S3 GetObject / exfil event, so the summary's "12 GB exfiltrated" claim is unsupported.
  - `pe_features.json` — PE feature record for the recovered dropper (carried over from Module 12);
    its SHA-256 is the ground truth for any hash the summary cites.

Naming is neutral and consistent with the rest of the track (`jsmith`, `svc-backup`, `prod-deploy`,
`BEACHHEAD-WS01`, C2 `workspacin.cloud`); the attack chain is modelled on the publicly documented
Lunar Spider / Latrodectus case
(<https://thedfirreport.com/2025/09/29/from-a-single-click-how-lunar-spider-enabled-a-near-two-month-intrusion/>).
See `../ANCHOR.md`.

## Optional REAL artifact (`make fetch-data`)

To practise tracing an AI-asserted CVE/technique to a **genuine** event log (additive — the committed
artifacts remain the default):

- **Dataset:** EVTX-ATTACK-SAMPLES (~200 real `.evtx` logs mapped to MITRE ATT&CK).
- **Author / source:** sbousseaden, <https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES> (GPL-3.0).
- **File wired:**

  | Purpose | File | Raw URL |
  |---|---|---|
  | Real Zerologon (CVE-2020-1472) NetLogon error — the anchor case's escalation technique | `Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Credential%20Access/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx |

- **Why this one:** the anchored Lunar Spider case used Zerologon (CVE-2020-1472) for lateral
  movement. A real Zerologon log lets the learner confirm a CVE claim against an actual artifact
  (Event ID 5805) instead of only against the seeded fixtures — the exact "trace the claim to a
  primary source" discipline the module teaches.
- **Fetch:** `make fetch-data` downloads it into `data/artifacts/`.

## SHA-256 (fill after fetch)

```
<fill after fetch>  data/artifacts/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx
```

## Notes

- The download is **deferred to runner-validation** — it was not run while authoring this lab.
  `make up && make demo` requires **no network** and uses only the committed fixtures; `make
  fetch-data` is the opt-in path to the real artifact.
