# Module 01 — Zero Trust Principles lab.
# No container needed: this is a document analysis exercise.
# Standard targets: demo / reset.
.PHONY: demo reset

demo:   ## Print scenario summary and expected gap categories
	@echo "============================================================"
	@echo "  Lab 01 — Zero Trust Gap Analysis: Meridian Financial"
	@echo "============================================================"
	@echo ""
	@echo "Scenario seed file: data/meridian-access-map.md"
	@echo "Read it, then produce gap-analysis.md."
	@echo ""
	@echo "NIST 800-207 pillars to assess:"
	@echo "  1. Identity"
	@echo "  2. Device"
	@echo "  3. Network"
	@echo "  4. Application / Workload"
	@echo "  5. Data"
	@echo ""
	@echo "Expected gap categories (spoilers — don't read until after step 2):"
	@echo "  - Identity : MFA only at VPN perimeter, not per-app (Traditional)"
	@echo "  - Device   : 25%% corporate + 100%% contractor have no EDR; no posture signal (Traditional)"
	@echo "  - Network  : Flat /20; no East-West inspection; no micro-segmentation (Traditional)"
	@echo "  - App      : Core banking + SWIFT reachable to all VPN users (Traditional)"
	@echo "  - Data     : No data classification or DLP; audit log gaps (Traditional)"
	@echo ""
	@echo "Deliverables: gap-analysis.md + score-zt.py"
	@echo "============================================================"

reset:  ## No-op for this lab (no containers)
	@echo "Nothing to reset — no containers in this lab."
