.PHONY: up down reset demo shell

up:        ## Build and start the MCP server
	docker compose up -d --build

down:      ## Stop containers
	docker compose down

reset:     ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

demo:      ## Call each MCP tool and show the JSON response
	@echo "=== MCP Server Demo — SOC Security Tools ==="
	@echo ""
	docker compose run --rm lab sh -c '\
		pip install -q requests 2>/dev/null; \
		python3 -c " \
import subprocess, json, sys; \
\
# Run the MCP server as a subprocess using stdio transport \
import threading, time; \
\
DATA_DIR = \"/lab/data\"; \
\
# Direct Python import (faster than subprocess in demo) \
sys.path.insert(0, \"/lab\"); \
import os; os.environ[\"DATA_DIR\"] = DATA_DIR; \
\
# Import and call tools directly for the demo \
from server.server import get_threat_intel, search_alerts, summarize_incident; \
\
print(\"--- Tool 1: get_threat_intel(185.220.101.42) ---\"); \
r = get_threat_intel(\"185.220.101.42\"); \
print(json.dumps(r, indent=2)); \
print(); \
\
print(\"--- Tool 2: search_alerts(PowerShell) ---\"); \
r = search_alerts(\"PowerShell\"); \
print(json.dumps(r, indent=2)); \
print(); \
\
print(\"--- Tool 3: summarize_incident(INC-2025-0042) ---\"); \
r = summarize_incident(\"INC-2025-0042\"); \
print(json.dumps(r, indent=2)); \
print(); \
\
print(\"--- Validation test: get_threat_intel with injection string ---\"); \
r = get_threat_intel(\"bad\'; DROP TABLE iocs;--\"); \
print(json.dumps(r, indent=2)); \
"'
