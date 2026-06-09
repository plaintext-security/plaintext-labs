# Module 02 — Cloud Identity & IAM lab.
# Standard targets: up / down / reset / demo / shell.
.PHONY: up down reset demo shell

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
