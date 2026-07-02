# Labs redesign — `feat/verdict-redesign`

This branch receives the **lab-environment** side of the curriculum redesign. The design, the type
library, and the conversion roadmap live in the **`plaintext`** repo:

- `plaintext/AUTHORING.md` — the type-driven authoring model (v2 contributing guide).
- `plaintext/planning/MODULE-TYPE-LIBRARY.md` — the 16 module/lab types + authoring templates.
- `plaintext/planning/REDESIGN-ROADMAP.md` — the sequenced conversion plan (waves).
- `plaintext/planning/type-pass/SYNTHESIS.md` — the per-track type map and gap analysis.

## What lands here, by wave

- **Wave 1** — validated lab envs for the promoted cloud & foundations "Verdict" tracks (the backfill
  items in each track's `STATUS.md`): new `make` targets, seed data, the cloud **KMS** lab, the
  foundations cert-check / beacon-capture / ECB-step additions.
- **Wave 2** — lab scaffolds for the four systemic constructs, especially the new ones that need real
  environments:
  - **Eval Harness (#13)** — a reusable pattern: a held-out labelled corpus + `make eval` (scorecard) +
    a CI **regression gate** fixture. Built first for ai-ops, then defensive/cloud/malware/AD detection.
  - **Migration (#12)** — multi-state environments that run **legacy and new side by side** (VPN→ZTNA,
    click-ops→IaC, classic→hybrid-PQC, unmanaged→managed fleet) with a proof-of-no-outage check.
- **Wave 3** — per-track lab conversions as each track is converted in `plaintext`.

## Bar for any lab here (unchanged)
`make up && make demo && make down` green on a Linux runner before adding `.ci-demo`; a `check.yaml`
using the check type the module's **type** maps to (see the library); check general solutions against a
**held-out** set, never the demo set (doubly true for Eval Harness labs). Keep generated artifacts
(captures, keys, dumps) out of git.
