# Lab 07 — Compliance Scoring & Auditing

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/07-compliance-auditing
make up        # build the deliberately un-hardened container
make demo      # run OpenSCAP + Lynis, apply one fix, re-run, show delta
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally. The container is intentionally un-hardened to show a meaningful delta.

## Scenario

Meridian Financial's internal audit team has requested a CIS compliance baseline for all Linux
application servers before the external PCI audit next quarter. You have been handed a server
image that has had no hardening applied. Your job: run the full audit cycle — baseline scan,
fix one finding, rescan — and produce structured evidence that the audit team can include in
their report package.

## Do

1. [ ] `make demo` — watch both OpenSCAP and Lynis run against the un-hardened container.
   Note: the OpenSCAP CIS Level 1 pass percentage, the Lynis hardening index, and the total
   number of failing rules. Record these as your "before" baseline.

2. [ ] `make shell` and run the OpenSCAP scan manually with HTML output:
   ```bash
   oscap xccdf eval \
     --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
     --results /tmp/results-before.xml \
     --report /tmp/report-before.html \
     /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml 2>&1 | tail -5
   ```
   Count the failing rules: `grep -c 'result>fail' /tmp/results-before.xml`

3. [ ] Identify the highest-severity failing rules from the OpenSCAP results.
   (Grep for `severity="high"` in the XML, or check the HTML report's severity column.)
   Choose a **set of 3–5** to remediate — this is a *scoring* exercise, so one rule won't show
   a meaningful delta.

4. [ ] Apply the remediation for **each** finding in your set, re-scanning after each one so you
   watch the score climb step by step. A good starting finding:
   ```bash
   # Disable USB storage (CIS rule: xccdf_..._rule_kernel_module_usb-storage_disabled)
   echo "install usb-storage /bin/true" >> /etc/modprobe.d/usb-storage.conf
   ```
   Pick 2–4 more (e.g. disabling unused filesystems/protocols, an `auditd` setting, a `sysctl`
   network-hardening control, a sticky-bit/permission fix). For each: document the finding ID, the
   remediation command, and the CIS control reference. Keep a running note of the failing-rule count
   (or pass percentage) after each fix so the *climb* is visible, not just the endpoints.

5. [ ] Re-run OpenSCAP and Lynis after the full set is applied. Save as `results-after.xml`.
   Compare: `grep -c 'result>fail' /tmp/results-after.xml` — confirm the count dropped by your
   3–5 remediated rules and the OpenSCAP pass percentage / Lynis hardening index rose accordingly.

6. [ ] Produce the delta report showing the climb across the set. From the container:
   ```bash
   # Count before and after failing rules
   before=$(grep -c 'result>fail' /tmp/results-before.xml)
   after=$(grep -c 'result>fail' /tmp/results-after.xml)
   echo "Before: $before failing | After: $after failing | Delta: $((before - after)) rules fixed"
   ```
   The delta should equal the number of findings you remediated (3–5), and your running note from
   step 4 should show the score rising fix-by-fix — that progression *is* the scoring evidence.

7. [ ] Write a one-page exception report for one finding you cannot remediate in the container
   environment. Format: Finding ID, CIS control, why it cannot be remediated, risk acceptance,
   compensating control.

## Success criteria — you're done when

- [ ] You have before/after OpenSCAP XML and Lynis output.
- [ ] A **set of 3–5 high-severity findings** moved from fail to pass, each with a documented remediation.
- [ ] You have a delta count (matching your remediated set) and a record of the score climbing fix-by-fix.
- [ ] You have a written exception report for one un-remediable finding.

## Deliverables

`compliance-evidence/` directory containing: `results-before.xml`, `results-after.xml`,
`delta-summary.md` (your delta count + the per-fix score climb across the 3–5 remediated findings +
remediation documentation), and `exception-report.md`. Commit the directory.

## Automate & own it

**Required.** Write a Python script `compliance-diff.py` that takes two OpenSCAP XML result
files as arguments, parses the rule results, and outputs a Markdown table showing: rule ID,
before status, after status, and severity. Have an AI draft the XML parsing code; you verify
the output against the raw XML before committing. This is the automated evidence-generation
tool for a continuous compliance pipeline.

## AI acceleration

Paste a failing OpenSCAP rule's XCCDF description into an AI and ask it for: what the rule
tests, the one-line remediation, and the CIS control reference. Cross-check the remediation
against the SCAP Security Guide rationale. Apply the fix and re-run the scan — did it move
from fail to pass? AI explains the finding; the rescan confirms the fix.

## Connects forward

The exception management process you practiced here (documented risk acceptances, compensating
controls) is the compliance governance layer that module 06 (configuration management) enforces
automatically — once you know what the exceptions are, they become Ansible variables that
configure a different posture for that host class. Module 10 (detecting host compromise) adds
the detection that compensates for controls you accepted as exceptions.

## Marketable proof

> "I ran OpenSCAP and Lynis against an un-hardened Linux host, produced structured before/after
> compliance evidence, and wrote exception reports with documented risk acceptances and
> compensating controls — the exact evidence package an external auditor reviews."

## Stretch

- Automate the full audit cycle as a scheduled GitHub Actions workflow: spin up the container,
  run the scan, parse the score, and post the delta as a PR comment or issue. This is a
  continuous compliance pipeline.
- Research how a SCAP remediation script (`oscap xccdf generate fix`) differs from your manual
  remediation — run it against the before state and check which findings it fixes correctly and
  which it gets wrong or misses.
