.PHONY: demo

demo:      ## Print the automation assessment framework
	@echo "=== SOC Automation Assessment Framework ==="
	@echo
	@echo "Axes:"
	@echo "  Repeatability: How often does this task occur? (daily / weekly / ad-hoc)"
	@echo "  Determinism:   Given the same inputs, is the answer always the same? (high / medium / low)"
	@echo
	@echo "Zones:"
	@echo "  FULL AUTOMATION:        High repeatability + High determinism"
	@echo "  HUMAN-IN-THE-LOOP:      High repeatability + Medium determinism"
	@echo "  KEEP MANUAL:            Low repeatability OR Low determinism (judgment required)"
	@echo
	@echo "ROI formula:"
	@echo "  ROI = (time_saved_min × frequency_per_week) - maintenance_burden_hrs_per_month"
	@echo
	@echo "Kill-switch requirement:"
	@echo "  Every automation must be stoppable within 60 seconds without a code change."
	@echo
	@echo "See data/automation-assessment.md for the full task list."
