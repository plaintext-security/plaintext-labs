# Module 02 — Cloud Identity & IAM lab.
# Standard targets: up / down / reset / demo / shell.
.PHONY: up down reset demo shell check-escalation check-fixed apply-fixed

up:        ## Build, seed, and start (LocalStack + lab container)
	docker compose up -d --build
	@echo "Waiting for seed to complete..."
	@docker compose wait seed || true
	@echo "Lab ready. Run: make shell  or  make demo"

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely (containers + local images + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Drop into the lab container (cloudfox + awslocal available)
	docker compose exec lab bash

# --- Worked example: enumerate IAM with cloudfox ----------------------------
demo:      ## Run the IAM enumeration walkthrough
	@docker compose run --rm lab sh -c '\
		echo "=== 1. List IAM users (awslocal) ==="; \
		awslocal iam list-users --query "Users[*].UserName" --output table; \
		echo; \
		echo "=== 2. List IAM roles (awslocal) ==="; \
		awslocal iam list-roles --query "Roles[*].[RoleName,AssumeRolePolicyDocument.Statement[0].Principal]" --output table; \
		echo; \
		echo "=== 3. cloudfox: enumerate permissions for dev-alice ==="; \
		cloudfox aws \
		  --endpoint http://localstack:4566 \
		  --profile localstack \
		  permissions \
		  --principal arn:aws:iam::000000000001:user/dev-alice \
		  --output table 2>/dev/null || \
		awslocal iam list-attached-user-policies --user-name dev-alice --output table; \
		echo; \
		echo "=== 4. MeridianAdminRole trust policy — spot the account-root trust ==="; \
		awslocal iam get-role --role-name MeridianAdminRole \
		  --query "Role.AssumeRolePolicyDocument" --output json; \
		echo; \
		echo "=== 5. CICD role trust — note missing sub condition ==="; \
		awslocal iam get-role --role-name MeridianCICDRole \
		  --query "Role.AssumeRolePolicyDocument" --output json; \
		echo; \
		echo "FINDING: dev-alice has iam:PassRole/* — can pass MeridianEC2AdminRole to a new EC2 instance."; \
		echo "FINDING: MeridianAdminRole trusts account root — any principal in the account can assume it via sts:AssumeRole."; \
		echo "FINDING: MeridianCICDRole OIDC trust has no sub condition — any GitHub Actions workflow can assume it."; \
	'
	@echo
	@echo "=== 6. Escalation BEFORE the fix (PassRole assertions show ALLOW = FAIL) ==="
	-docker compose run --rm lab python3 check_escalation.py data/dev-alice-policy.json
	@echo
	@echo "=== 7. Escalation AFTER the fix (reference scoped PassRole — all PASS) ==="
	docker compose run --rm lab python3 check_escalation.py data/dev-alice-fixed-policy.json

# --- Remediation: author the least-privilege fix, then prove it -------------
check-escalation: ## Check the ORIGINAL dev-alice policy — expect the PassRole escalation to FAIL
	docker compose run --rm lab python3 check_escalation.py data/dev-alice-policy.json

check-fixed:      ## Check YOUR dev-alice-fixed-policy.json — aim for all PASS
	docker compose run --rm lab python3 check_escalation.py data/dev-alice-fixed-policy.json

apply-fixed:      ## Apply your fixed policy to LocalStack as a new default version, then re-enumerate
	@docker compose run --rm lab sh -c '\
		ARN=arn:aws:iam::000000000001:policy/MeridianDevPolicy; \
		awslocal iam create-policy-version --policy-arn $$ARN \
		  --policy-document file:///lab/data/dev-alice-fixed-policy.json --set-as-default >/dev/null && \
		echo "Applied fixed policy as new default version."; \
		echo "dev-alice attached policies now:"; \
		awslocal iam list-attached-user-policies --user-name dev-alice --output table'
