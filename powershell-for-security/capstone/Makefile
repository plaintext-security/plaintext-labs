.PHONY: up down reset shell accept test eval

up:        ## Build and start the capstone container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a pwsh shell in the container
	docker compose exec lab pwsh

accept:    ## Run the structural acceptance checks (manifest, exports, analyzer, stub progress)
	docker compose run --rm lab pwsh -NoProfile -File ./accept.ps1

test:      ## Run the Pester suite (fill in the -Pending stubs as you build)
	docker compose run --rm lab pwsh -NoProfile -Command "Invoke-Pester -Path ./tests -Output Detailed"

eval:      ## Run the detection eval (implement eval.ps1 first)
	docker compose run --rm lab pwsh -NoProfile -File ./eval.ps1
