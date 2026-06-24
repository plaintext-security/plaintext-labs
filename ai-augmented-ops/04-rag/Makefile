.PHONY: up down reset demo shell ingest query

OLLAMA_MODEL ?= tinyllama

up:        ## Start all containers and pull required models
	docker compose up -d
	@echo "Waiting for services and pulling models (this may take a few minutes)..."
	@docker compose run --rm lab sh -c '\
		pip install -q requests chromadb==0.5.23 2>/dev/null; \
		python3 -c " \
import requests, time; \
for svc, url in [(\"Ollama\",\"http://ollama:11434/api/tags\"),(\"ChromaDB\",\"http://chromadb:8000/api/v1/heartbeat\")]: \
    for i in range(30): \
        try: requests.get(url, timeout=2); print(svc+\" ready.\"); break \
        except: time.sleep(2) \
    else: print(svc+\" not ready!\") \
print(\"Pulling tinyllama...\"); \
requests.post(\"http://ollama:11434/api/pull\", json={\"name\":\"tinyllama\"}, timeout=600); \
print(\"Pulling nomic-embed-text...\"); \
requests.post(\"http://ollama:11434/api/pull\", json={\"name\":\"nomic-embed-text\"}, timeout=600); \
print(\"Models ready.\") \
"'

down:      ## Stop containers
	docker compose down

reset:     ## Tear down completely (containers + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

ingest:    ## Ingest the knowledge base into ChromaDB
	docker compose run --rm lab sh -c 'pip install -q requests chromadb==0.5.23 2>/dev/null && python3 scripts/ingest.py'

query:     ## make query Q="your question here"
	docker compose run --rm lab sh -c 'pip install -q requests chromadb==0.5.23 2>/dev/null && python3 scripts/query.py "$(Q)"'

demo:      ## Ingest the knowledge base and run the demo query
	@echo "=== RAG Demo — LastPass 2022 Breach Knowledge Base ==="
	@docker compose run --rm lab sh -c '\
		pip install -q requests chromadb==0.5.23 2>/dev/null; \
		echo "Step 1: Ingesting knowledge base..."; \
		python3 scripts/ingest.py; \
		echo; \
		echo "Step 2: Running demo query..."; \
		python3 scripts/query.py "How did the attacker access the cloud backup storage in the LastPass breach?"'
