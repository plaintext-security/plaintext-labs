# Lab 02 — Windows Hardening to CIS

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships support files in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/02-windows-hardening
make demo      # runs score_report.py against sample CIS-CAT before/after JSON
```

**Windows VM required** for the full exercise (the hardening steps run on a real Windows 11 host).
The container element — `score_report.py` — runs on any platform and parses CIS-CAT Lite JSON
exports to show a before/after compliance delta.

For the VM: use a Windows 11 evaluation image from [Microsoft Evaluation Center](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-11-enterprise) (free, 90-day eval). Snapshot before applying any changes.

> Only apply hardening to VMs you own or control. Never apply LGPO settings to a production host
> without testing and change-management approval.

## Scenario

Meridian Financial's new CIS hardening programme starts with Windows 11 analyst workstations.
You have been handed a freshly built Windows 11 VM with no hardening applied. Your job:
run a CIS-CAT Lite baseline scan, apply a representative set of Level 1 controls using LGPO
and PowerShell, rescan, and produce a delta report that the security team can present to the audit committee.

## Do

**On your Windows VM:**

1. [ ] Download [CIS-CAT Lite](https://www.cisecurity.org/) from CIS and
   navigate to the Assessments section to find the CAT Lite tool. Run `CIS-CAT-Lite.bat` against your Windows 11 host.
   Export the JSON report as `cis-report-before.json`. Note your baseline score.

2. [ ] Open `data/lgpo-commands.ps1` from the lab directory. Review each command and the CIS
   control it addresses (the comment above each block). Run the script in an elevated PowerShell
   session: `.\data\lgpo-commands.ps1`. Do not just execute it blindly — read each section first.

3. [ ] Open `data/cis-windows-checklist.md` and manually apply the three controls marked
   **[MANUAL]** (they cannot be set via PowerShell alone). Each has exact instructions.

4. [ ] Rerun CIS-CAT Lite and export `cis-report-after.json`.

**Score reporting (any platform, including Mac/Linux):**

5. [ ] From the `plaintext-labs/endpoint-hardening/02-windows-hardening` directory:
   ```bash
   make demo
   ```
   This runs `score_report.py` against the sample before/after JSON files shipped in `data/`.
   Review the output format — it shows per-control pass/fail delta and the overall score improvement.

6. [ ] Copy your real `cis-report-before.json` and `cis-report-after.json` from the VM into
   `data/` and re-run `python3 score_report.py data/cis-report-before.json data/cis-report-after.json`.
   How many controls moved from fail to pass?

7. [ ] Identify the top three controls that still fail after your changes. Read their benchmark
   rationale and document *why* each is failing — is it a GPO that didn't apply, a setting that
   requires a reboot, or a control your environment legitimately can't meet?

## Success criteria — you're done when

- [ ] You have a before/after CIS-CAT JSON pair (real or sample) with a measurable score delta.
- [ ] `score_report.py` runs cleanly and shows per-control status.
- [ ] You can explain what each PowerShell block in `lgpo-commands.ps1` does and which CIS control it addresses.
- [ ] You have written up three failing controls with root-cause analysis.

## Deliverables

`score_report.md` — the delta output annotated with your root-cause notes on failing controls.
`lgpo-commands.ps1` — your hardening script (the version from `data/`, reviewed and initialled). Commit both.

## Automate & own it

**Required.** Extend `score_report.py` to accept a threshold argument (`--min-score 75`) and exit
non-zero if the after-score is below the threshold. Wire this into a CI check — a GitHub Actions
workflow that runs the scorer on every PR and blocks merge if the score drops. Have an AI draft
the threshold logic; you verify the exit code behaviour with `echo $?` before committing.

## AI acceleration

Paste a failing CIS control's description into an AI assistant and ask it to generate the
PowerShell registry path and value that would satisfy it. Then cross-check the output against
the CIS Benchmark PDF — does the path and value match the benchmark's "remediation" section
exactly? AI is fast at mechanical translation; the benchmark is the authority.

## Connects forward

The CIS baseline you establish here is the *measured* starting point for module 06 (Configuration
Management — expressing it as Ansible code) and module 07 (Compliance Scoring — automating the
measurement). Module 09 (privilege-escalation defense) revisits specific Level 2 controls that
close privesc paths.

## Marketable proof

> "I applied CIS Windows Level 1 controls using LGPO and PowerShell, scanned with CIS-CAT Lite,
> and built a CI-ready scoring script that fails a build when the compliance score drops below
> threshold."

## Stretch

- Apply a Level 2 control that breaks a piece of software (e.g. disabling NTLM breaks a legacy
  application). Document the finding and the compensating control you'd propose — this is the
  real-world hardening negotiation.
- Export the GPO backup with LGPO (`LGPO.exe /b <path>`) and commit the backup to git. Verify
  you can restore it to a fresh VM with a single command.
