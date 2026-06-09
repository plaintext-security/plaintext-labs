# Module 04 — ZTNA Architectures lab.
# No container needed: this is a design and document exercise.
# Standard targets: demo / reset.
.PHONY: demo reset

demo:   ## Print the Meridian scenario brief and point to seed materials
	@echo "============================================================"
	@echo "  Lab 04 — ZTNA Architecture Decision: Meridian Financial"
	@echo "============================================================"
	@echo ""
	@echo "Seed file: data/architecture-comparison.md"
	@echo "  Read it fully before starting the ADR exercise."
	@echo ""
	@echo "Meridian constraints summary:"
	@echo "  - 60%% SaaS / 30%% on-prem / 10%% Azure"
	@echo "  - 800 employees (60%% remote) + 120 BYOD contractors"
	@echo "  - 3 security engineers; no network team"
	@echo "  - Okta SSO; CrowdStrike on 75%% of corporate devices"
	@echo "  - PCI-DSS + SOX; SWIFT gateway must have per-request audit"
	@echo "  - Cannot re-architect core banking in 18 months"
	@echo "  - Must show ZT progress in 6 months; full migration in 24"
	@echo ""
	@echo "Patterns to evaluate:"
	@echo "  1. VPN (baseline)"
	@echo "  2. Reverse proxy (Pomerium)"
	@echo "  3. Network mesh (headscale/Tailscale)"
	@echo "  4. Cloud edge (Cloudflare Zero Trust)"
	@echo "  5. Hybrid (Cloudflare + headscale) — optional stretch"
	@echo ""
	@echo "Deliverable: architecture-adr.md (ADR: Context / Decision / Consequences)"
	@echo "Automate:   score-architecture.py (YAML-in → ranked patterns out)"
	@echo "============================================================"

reset:  ## No-op for this lab (no containers)
	@echo "Nothing to reset — no containers in this lab."
