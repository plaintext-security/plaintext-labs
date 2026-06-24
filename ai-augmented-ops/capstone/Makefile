# AI-Augmented Security Operations capstone — starter scaffold.
#
# This is a SKELETON, not a solution. `up`/`shell` give you a running stack
# (Ollama + ChromaDB + a lab container with the stub MCP server and seed
# runbooks) so you can start building your copilot under submission/ instead of
# wiring infrastructure. Grade yourself against rubric.md — no tool grades you.
#
# Targets:
#   make up      start Ollama + ChromaDB + lab container, pull the model
#   make shell   drop into the lab container (your build environment)
#   make tool    run the stub MCP server's self-test (no MCP client needed)
#   make down    stop and remove the stack
#   make grade   print rubric.md (advisory self-grade)

OLLAMA_MODEL ?= tinyllama
EMBED_MODEL  ?= nomic-embed-text

.PHONY: up shell tool down grade help

help:
	@echo "Capstone scaffold — see the Makefile header for targets."
	@echo "  make up | shell | tool | down | grade"

up:
	docker compose up -d
	@echo "Waiting for Ollama..."
	@until docker compose exec -T ollama ollama list >/dev/null 2>&1; do sleep 2; done
	docker compose exec -T ollama ollama pull $(OLLAMA_MODEL)
	docker compose exec -T ollama ollama pull $(EMBED_MODEL)
	@echo ""
	@echo "Stack is up. Generation model: $(OLLAMA_MODEL); embeddings: $(EMBED_MODEL)."
	@echo "Seed runbooks: data/runbooks/ . Stub MCP tool: tools/incident_tool.py ."
	@echo "Build your copilot under submission/.  ->  make shell"

shell:
	docker compose exec lab bash

# Self-test the stub MCP tool inside the lab container (installs deps on first run).
tool:
	docker compose exec -T lab python3 tools/incident_tool.py --selftest

down:
	docker compose down -v

grade:
	@cat rubric.md
