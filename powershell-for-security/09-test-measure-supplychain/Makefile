.PHONY: up down reset demo shell eval

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a pwsh shell in the lab container
	docker compose exec lab pwsh

eval:      ## Run just the detection eval (held-out scorecard + regression gate)
	docker compose run --rm lab pwsh -NoProfile -File ./eval.ps1

demo:      ## Run the full gate: PSScriptAnalyzer + Pester (coverage) + eval + sign/verify
	docker compose run --rm lab pwsh -NoProfile -File ./gate.ps1
