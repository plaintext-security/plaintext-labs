.PHONY: up down reset demo shell ask ingest

OLLAMA_MODEL ?= tinyllama
Q ?= Is 192.0.2.66 malicious?

up:        ## Start all containers and pull required models
	docker compose up -d
	@echo "Pulling models and ingesting knowledge base..."
	@docker compose run --rm copilot sh -c '\
		pip install -q requests chromadb==0.5.23 2>/dev/null; \
		python3 -c " \
import requests, time; \
for svc, url in [(\"Ollama\",\"http://ollama:11434/api/tags\"),(\"ChromaDB\",\"http://chromadb:8000/api/v1/heartbeat\")]: \
    for i in range(30): \
        try: requests.get(url, timeout=2); print(svc+\" ready.\"); break \
        except: time.sleep(2) \
requests.post(\"http://ollama:11434/api/pull\", json={\"name\":\"tinyllama\"}, timeout=600); \
requests.post(\"http://ollama:11434/api/pull\", json={\"name\":\"nomic-embed-text\"}, timeout=600); \
print(\"Models ready.\") \
"' && make ingest

down:      ## Stop containers
	docker compose down

reset:     ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the copilot container
	docker compose exec copilot bash

ingest:    ## Ingest the knowledge base into ChromaDB
	docker compose run --rm copilot sh -c 'pip install -q requests chromadb==0.5.23 2>/dev/null && python3 scripts/ingest.py'

demo:      ## Run the demo question: Is 192.0.2.66 malicious?
	@echo "=== SoC Copilot Demo ==="
	docker compose run --rm copilot sh -c '\
		pip install -q requests chromadb==0.5.23 2>/dev/null; \
		python3 copilot/copilot.py "Is 192.0.2.66 malicious?"'

ask:       ## make ask Q="your question here"
	docker compose run --rm copilot sh -c '\
		pip install -q requests chromadb==0.5.23 2>/dev/null; \
		python3 copilot/copilot.py "$(Q)"'
