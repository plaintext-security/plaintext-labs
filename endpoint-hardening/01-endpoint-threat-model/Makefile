# Module 01 — Threat Model of the Endpoint
# No container required — design exercise.
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

up:
	@echo "Module 01 is a design exercise — no container to start."
	@echo "Open data/endpoint-profile.md and data/threat-model-template.md"

down:
	@echo "Nothing to stop."

reset:
	@echo "Nothing to reset. Your work is in threat-model.md (not tracked by make)."

demo:
	@echo ""
	@echo "=========================================================="
	@echo "  Financial-Services Org — Endpoint Threat Model Exercise"
	@echo "=========================================================="
	@echo ""
	@echo "HOSTS IN SCOPE:"
	@echo "  Host A: Finance analyst workstation (Windows 11, domain-joined)"
	@echo "  Host B: Payroll API server (Ubuntu 22.04)"
	@echo ""
	@echo "REAL-WORLD ANCHOR (Colonial Pipeline, May 2021 / DarkSide):"
	@echo "  Initial access = compromised VPN account, NO MFA (ATT&CK T1078.002)"
	@echo "  The profile reproduces this gap (no MFA on VPN; stale contractor account)."
	@echo "  Make 'close the Colonial Pipeline path' one of your top-5 priorities."
	@echo ""
	@echo "CROWN JEWELS:"
	@echo "  - Domain credentials cached in LSASS (workstation)"
	@echo "  - Salary data in Excel files and Outlook OST (workstation)"
	@echo "  - Citrix session tokens (pivot to core banking)"
	@echo "  - PostgreSQL password in plaintext config (app server)"
	@echo "  - TLS private key (impersonation/MITM)"
	@echo ""
	@echo "ATTACKER PLAYBOOK (commodity ransomware):"
	@echo "  Phishing → code execution → LSASS dump → lateral movement → data encryption"
	@echo ""
	@echo "ATTACKER PLAYBOOK (targeted financial fraud):"
	@echo "  Phishing → persistence → payroll API access → salary manipulation"
	@echo ""
	@echo "YOUR TASK:"
	@echo "  1. Open data/endpoint-profile.md — read both host profiles"
	@echo "  2. Open data/threat-model-template.md — fill in assets, paths, mitigations"
	@echo "  3. Produce threat-model.md — your completed threat model"
	@echo "  4. Identify your top-5 hardening priorities"
	@echo ""
	@echo "SCORING RUBRIC:"
	@echo "  Assets:      >= 8 assets identified (L/M/H + adversary use)"
	@echo "  Paths:       >= 5 attack paths with ATT&CK IDs"
	@echo "  Mitigations: >= 5 with CIS or ATT&CK references"
	@echo "  Top-5:       ranked with reasoning"
	@echo ""

shell:
	@echo "No container for this module. Open your editor."
