# Module 14 — Data, the Last Pillar lab.
# Requires: docker
# Standard targets: up / down / reset / demo / shell / eval / test / detect / convert / check / ci
.PHONY: up down reset demo shell opa-shell eval test detect convert check ci

up:        ## Build the sigma image and start the OPA server
	docker compose up -d --build
	@echo "OPA server running on http://localhost:8181"
	@echo "Run: make demo"

down:      ## Stop containers
	docker compose down

reset:     ## Tear down completely (containers + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the sigma/detect.py container
	docker compose run --rm sigma bash

opa-shell: ## Open an interactive OPA REPL loaded with the lab policies
	# The OPA image is distroless (no shell). The interactive surface is the
	# OPA REPL itself — load the policy and experiment with `data.corp.data...`.
	docker compose run --rm opa-lab run /lab/data/policies/

# ── Demo — the "what good looks like" walk-through ────────────────────────────
demo:      ## Run the OPA classification scenarios, then the bulk-read Sigma detection
	@echo "========================================================"
	@echo "  PART 1 — Label-based authorization (OPA / Rego)"
	@echo "========================================================"
	@echo ""
	@echo "-- analyst reads public (expect: allow=true) --"
	docker compose run --rm opa-lab eval \
	  --input /lab/data/inputs/analyst-read-public.json \
	  --data /lab/data/policies/data-classification.rego \
	  "data.corp.data.allow"
	@echo ""
	@echo "-- analyst reads restricted (expect: allow=false, deny=true) --"
	docker compose run --rm opa-lab eval \
	  --input /lab/data/inputs/analyst-read-restricted.json \
	  --data /lab/data/policies/data-classification.rego \
	  "data.corp.data.allow"
	docker compose run --rm opa-lab eval \
	  --input /lab/data/inputs/analyst-read-restricted.json \
	  --data /lab/data/policies/data-classification.rego \
	  "data.corp.data.deny"
	@echo ""
	@echo "-- data-officer reads restricted (expect: allow=true) --"
	docker compose run --rm opa-lab eval \
	  --input /lab/data/inputs/data-officer-read-restricted.json \
	  --data /lab/data/policies/data-classification.rego \
	  "data.corp.data.allow"
	@echo ""
	@echo "-- FAIL-CLOSED: analyst reads an unlabeled record (expect: effective_classification=restricted, deny=true) --"
	docker compose run --rm opa-lab eval \
	  --input /lab/data/inputs/analyst-read-unlabeled.json \
	  --data /lab/data/policies/data-classification.rego \
	  "data.corp.data.effective_classification"
	docker compose run --rm opa-lab eval \
	  --input /lab/data/inputs/analyst-read-unlabeled.json \
	  --data /lab/data/policies/data-classification.rego \
	  "data.corp.data.deny"
	@echo ""
	@echo "========================================================"
	@echo "  PART 2 — Exfil detection (Sigma / bulk restricted reads)"
	@echo "========================================================"
	@echo ""
	@echo "-- Rule: examples/zt-bulk-restricted-read.yml over data/access-logs.jsonl --"
	@echo "   Expect: silent on dpatel's normal daytime session (3 restricted reads),"
	@echo "   ONE hit-group on dpatel's 8-read overnight session (sess_D2)."
	docker compose run --rm sigma python detect.py \
	  examples/zt-bulk-restricted-read.yml data/access-logs.jsonl

# ── Your turn: point these at the rule/policy you're working on ──────────────
eval:      ## make eval POLICY=<path> INPUT=<path> — one-off opa eval
	docker compose run --rm opa-lab eval \
	  --input /lab/$(INPUT) \
	  --data /lab/$(POLICY) \
	  "data"

test:      ## Run opa test over every policy in data/policies/
	@echo "== Running OPA policy tests =="
	docker compose run --rm opa-lab test /lab/data/policies/ -v

detect:    ## make detect RULE=your-rule.yml — run a Sigma rule against the access log
	docker compose run --rm sigma python detect.py $(RULE) data/access-logs.jsonl

convert:   ## make convert RULE=your-rule.yml — convert a Sigma rule to SPL
	docker compose run --rm sigma sigma convert -t splunk -p sysmon $(RULE)

# ── Regression gate ────────────────────────────────────────────────────────
check:     ## Run the committed regression test (deny path + detection firing)
	bash check-data.sh

ci:        ## Run opa test (used in CI / GitHub Actions)
	docker compose run --rm --no-deps opa-lab test /lab/data/policies/ -v
