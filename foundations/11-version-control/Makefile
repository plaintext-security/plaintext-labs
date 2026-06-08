.PHONY: demo scan

# Check git + print portfolio setup guide and secret-hygiene instructions
demo:
	python3 check.py

# Scan current directory for secrets with gitleaks
scan:
	python3 check.py --scan
