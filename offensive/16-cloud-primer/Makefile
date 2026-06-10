.PHONY: demo check

# Validate connectivity to flaws.cloud and print walkthrough structure
demo:
	python3 check.py

# Also verify AWS CLI is configured (needed for CloudGoat path)
check:
	python3 check.py --aws
