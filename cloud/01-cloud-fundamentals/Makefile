# Module 01 — Cloud Fundamentals & Shared Responsibility lab.
# Standard targets every reference lab provides: up / down / reset / demo / shell.
.PHONY: up down reset demo shell check

up:        ## Build, seed, and start (LocalStack + lab container)
	docker compose up -d --build
	@echo "Waiting for seed to complete..."
	@docker compose wait seed || true
	@echo "Lab ready. Run: make shell"

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely (containers + local images + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Drop into the lab container (awscli pointed at LocalStack)
	docker compose exec lab bash

# --- Worked example: enumerate the seeded account ----------------------------
demo:      ## Run the enumeration walkthrough deterministically
	@docker compose run --rm lab sh -c '\
		echo "=== 1. List IAM users ==="; \
		awslocal iam list-users --query "Users[*].[UserName,Arn]" --output table; \
		echo; \
		echo "=== 2. Policies attached to dev-alice ==="; \
		awslocal iam list-attached-user-policies --user-name dev-alice --output table; \
		echo; \
		echo "=== 3. MeridianDevPolicy document (spot the wildcards) ==="; \
		POLICY_ARN=$$(awslocal iam list-policies --scope Local \
		  --query "Policies[?PolicyName==\`MeridianDevPolicy\`].Arn" --output text); \
		VID=$$(awslocal iam get-policy --policy-arn $$POLICY_ARN \
		  --query "Policy.DefaultVersionId" --output text); \
		awslocal iam get-policy-version --policy-arn $$POLICY_ARN --version-id $$VID \
		  --query "PolicyVersion.Document" --output json; \
		echo; \
		echo "=== 4. EC2 instance role trust policy ==="; \
		awslocal iam get-role --role-name MeridianEC2InstanceRole \
		  --query "Role.AssumeRolePolicyDocument" --output json; \
		echo; \
		echo "=== 5. S3 public-access-block settings ==="; \
		awslocal s3api get-public-access-block --bucket meridian-uploads-dev --output json; \
		echo; \
		echo "FINDINGS: wildcards in MeridianDevPolicy (s3:* + iam:PassRole/*), public-access-block disabled."; \
	'

# --- Prerequisite check (no container needed) --------------------------------
check:     ## Verify that docker and docker compose are available
	@docker --version
	@docker compose version
	@echo "Tooling OK. Run: make up"
