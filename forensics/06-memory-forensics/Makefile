# Module 06 — Memory Forensics lab.
# Standard targets: up / down / reset / demo / shell / analyze / fetch-data
.PHONY: up down reset demo shell analyze fetch-data

up:  ## Build and start the Volatility3 container
	docker compose up -d --build

# The real artifact is MemLabs Lab 1 "Beginner's Luck" — a ~1GB Windows memory dump that is
# Google-Drive-hosted via the repo's per-lab README. We do NOT guess a Drive URL: this target
# prints the instructions to fetch it manually. See PROVENANCE.md.
fetch-data:  ## Print instructions to fetch the real MemLabs Lab 1 memory image
	@if [ -f data/memory.img ]; then \
		echo "exists: data/memory.img"; \
	else \
		echo "MemLabs Lab 1 \"Beginner's Luck\" memory image is ~1GB and Google-Drive-hosted."; \
		echo "Fetch it manually (do not trust any guessed Drive URL):"; \
		echo "  1. Open https://github.com/stuxnet999/MemLabs"; \
		echo "  2. Go to Lab 1 (folder: 'MemLabs Lab Setup') and follow its README"; \
		echo "     download link to the Drive-hosted image."; \
		echo "  3. Unzip and place the dump at: data/memory.img  (gitignored, not committed)"; \
		echo "  4. Run: make analyze IMAGE=data/memory.img"; \
		echo "Record the SHA-256 in PROVENANCE.md after download."; \
	fi

down:  ## Stop and remove the container
	docker compose down

reset:  ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:  ## Open a shell in the lab container
	docker compose exec lab bash

demo:  ## Analyze pre-processed Volatility3 output from data/memory-sample.json
	docker compose run --rm lab python3 analyze_memory.py

# To analyze a real memory image, place it at data/memory.img and run:
#   make analyze IMAGE=data/memory.img
analyze:  ## Run Volatility3 plugins against a real memory image (make analyze IMAGE=path/to/image)
	@if [ -z "$(IMAGE)" ]; then \
		echo "Usage: make analyze IMAGE=data/memory.img"; \
		exit 1; \
	fi
	docker compose run --rm lab sh -c '\
		echo "=== pslist ==="; \
		vol -f $(IMAGE) windows.pslist; \
		echo; \
		echo "=== pstree ==="; \
		vol -f $(IMAGE) windows.pstree; \
		echo; \
		echo "=== cmdline ==="; \
		vol -f $(IMAGE) windows.cmdline; \
		echo; \
		echo "=== netscan ==="; \
		vol -f $(IMAGE) windows.netscan; \
		echo; \
		echo "=== malfind ==="; \
		vol -f $(IMAGE) windows.malfind'
