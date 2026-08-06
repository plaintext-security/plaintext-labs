# Module 01 — Cloud Fundamentals & Shared Responsibility lab.
# Standard targets every reference lab provides: up / down / reset / demo / shell.
# Runs on floci (free local AWS emulator). `aws` honors AWS_ENDPOINT_URL, so no LocalStack-branded wrapper.
.PHONY: up down reset demo shell check

up:        ## Build, seed, and start (floci + lab container)
	docker compose up -d --build
	@echo "Waiting for seed to complete..."
	@docker compose wait seed || true
	@echo "Lab ready. Run: make shell  or  make demo"

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely (containers + local images + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Drop into the lab container (aws pointed at floci)
	docker compose exec lab bash

# --- Worked example: enumerate the seeded account ----------------------------
demo:      ## Run the enumeration walkthrough deterministically
	@docker compose run --rm lab sh -c '\
		echo "=== 1. List IAM users ==="; \
		aws iam list-users --query "Users[*].[UserName,Arn]" --output table; \
		echo; \
		echo "=== 2. Policies attached to dev-alice ==="; \
		aws iam list-attached-user-policies --user-name dev-alice --output table; \
		echo; \
		echo "=== 3. DevPolicy document (spot the wildcards) ==="; \
		POLICY_ARN=$$(aws iam list-policies --scope Local \
		  --query "Policies[?PolicyName==\`DevPolicy\`].Arn" --output text); \
		VID=$$(aws iam get-policy --policy-arn $$POLICY_ARN \
		  --query "Policy.DefaultVersionId" --output text); \
		aws iam get-policy-version --policy-arn $$POLICY_ARN --version-id $$VID \
		  --query "PolicyVersion.Document" --output json; \
		echo; \
		echo "=== 4. EC2 instance role trust policy ==="; \
		aws iam get-role --role-name EC2InstanceRole \
		  --query "Role.AssumeRolePolicyDocument" --output json; \
		echo; \
		echo "=== 5. S3 public-access-block settings ==="; \
		aws s3api get-public-access-block --bucket uploads-dev --output json; \
		echo; \
		echo "FINDINGS: wildcards in DevPolicy (s3:* + iam:PassRole/*), public-access-block disabled."; \
	'

# --- Prerequisite check (no container needed) --------------------------------
check:     ## Verify that docker and docker compose are available
	@docker --version
	@docker compose version
	@echo "Tooling OK. Run: make up"
