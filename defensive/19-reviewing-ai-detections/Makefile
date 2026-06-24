# Module 19 — Reviewing AI Detections lab.
# Standard targets every reference lab provides: up / down / reset / shell / demo.
.PHONY: up down reset shell demo review convert reveal

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- Worked example (the "what good looks like" demo) ---------------------
demo:      ## Show one drafted rule convert cleanly, then FAIL to fire — the tell
	docker compose run --rm lab sh -c '\
		echo "== 1. The AI draft converts to SPL with no error =="; \
		sigma convert -t splunk -p sysmon ai-drafts/01_encoded_powershell.yml || true; \
		echo; \
		echo "== 2. ...but fire it at the labelled corpus and it catches NOTHING =="; \
		echo "   (wrong field: ProcessCommandLine vs. the estate'"'"'s CommandLine)"; \
		python review.py --corpus corpus/corpus.jsonl --attack attack/attack_ids.txt \
			ai-drafts/01_encoded_powershell.yml || true; \
		echo; \
		echo "== 3. Review the whole AI batch: which drafts misfire? =="; \
		python review.py --corpus corpus/corpus.jsonl --attack attack/attack_ids.txt \
			ai-drafts/*.yml || true'

# --- Your turn ------------------------------------------------------------
review:    ## make review RULES="fixed/*.yml" — fire your fixed rules at the corpus
	docker compose run --rm lab python review.py \
		--corpus corpus/corpus.jsonl --attack attack/attack_ids.txt $(RULES)

convert:   ## make convert RULE=ai-drafts/01_....yml — convert a rule to SPL
	docker compose run --rm lab sigma convert -t splunk -p sysmon $(RULE)

reveal:    ## Unseal the answer key — only AFTER your own review is committed
	@echo ">>> Spoiler: the planted-error answer key. Commit your review first."
	docker compose run --rm lab cat solution/findings.md
