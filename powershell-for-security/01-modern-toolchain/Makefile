.PHONY: up down reset demo shell

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a pwsh shell in the lab container
	docker compose exec lab pwsh

demo:      ## Run the module gate (PSScriptAnalyzer + Pester) over the reference migrated module
	docker compose run --rm lab pwsh -NoProfile -File ./gate.ps1
