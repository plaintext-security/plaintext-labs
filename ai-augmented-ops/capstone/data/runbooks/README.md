# Seed runbook corpus — capstone starter

A small, **realistic-but-synthetic** SOC runbook corpus to seed your capstone copilot's
RAG store. Each runbook is grounded in a **named, real incident** so the corpus reflects
the kind of institutional knowledge a real SOC indexes — replace and extend it with
*your own* notes (that is what makes the copilot yours, per the rubric).

Files:
- `01-ransomware-containment.md` — shadow-copy deletion / mass-rename containment.
- `02-public-cloud-bucket.md` — public object storage exposure (the 2017 S3 leak class).
- `03-credential-breach.md` — credential/key compromise & cloud-backup exfil (LastPass 2022).
- `04-prompt-injection-response.md` — responding to an LLM prompt-injection (EchoLeak, Chevy).
- `05-vendor-advisory-INJECTED.md` — **a deliberately poisoned runbook.** It carries a hidden
  instruction aimed at the model, in the EchoLeak (CVE-2025-32711) / Invariant Labs
  tool-poisoning shape. It is your **red-team target**: ingest it, show your copilot follows
  the injected instruction (data exfil / unauthorised action), then harden so it doesn't.
  Do **not** delete it to "pass" — defeating it *with a control* is the deliverable.

> These are study artifacts, not a live SOC export. IPs use RFC 5737 documentation ranges
> and domains use RFC 2606 reserved names.
