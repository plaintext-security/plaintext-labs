# Module 17 — KEV-Driven Defense lab.
# Standard targets every reference lab provides: up / down / reset / demo.
# The `demo` is offline & deterministic (bundled KEV snapshot + bundled access log)
# so it passes in CI; `refresh` and the `target-*` helpers reach the live internet.
.PHONY: up down reset shell demo refresh recommend detect target-up target-down grade

up:        ## Build and start the analysis container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- The worked example ("what good looks like") -------------------------------
demo:      ## Show the KEV→Vulhub picture, surface the reference target, then detect its exploit
	docker compose run --rm lab sh -c '\
		echo "== 1. Refresh against the CISA KEV snapshot: which entries can we stand up? =="; \
		python kev_refresh.py --limit 12; \
		echo; \
		echo "== 2. The lab ships a worked exploit+detection for this reference target =="; \
		python kev_refresh.py --reference; \
		echo; \
		echo "== 3. Detect that exploit (Log4Shell JNDI) in the captured access log =="; \
		python detect.py data/solr_access.log'

# --- Live + your-turn helpers --------------------------------------------------
refresh:   ## Rank TODAY'S live CISA KEV catalog (needs internet)
	docker compose run --rm lab python kev_refresh.py --live

recommend: ## Print the single best runnable target (live)
	docker compose run --rm lab python kev_refresh.py --live --recommend

detect:    ## make detect LOG=path — run the detection against your own capture
	docker compose run --rm lab python detect.py $(LOG)

# --- The exploit target (Vulhub) — pulled on demand, not committed -------------
# Stands up the recommended Vulhub environment so you can actually exploit it.
# Requires Docker Hub access (Vulhub images live there). Clones into ./target/.
target-up: ## Clone + start the recommended Vulhub target (Log4Shell / Solr on :8983)
	@test -d target/vulhub || git clone --depth 1 https://github.com/vulhub/vulhub target/vulhub
	cd target/vulhub/log4j/CVE-2021-44228 && docker compose up -d
	@echo "Target up: http://localhost:8983/solr/  (exploit it, then re-run detect on its logs)"

target-down: ## Stop the Vulhub target
	@cd target/vulhub/log4j/CVE-2021-44228 && docker compose down || true

.PHONY: grade
grade:     ## Grade your work against grade.yaml (writes receipt.json on pass)
	python3 ../../scripts/grade.py grade.yaml
