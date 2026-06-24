.PHONY: up down reset demo shell create-image fetch-data

# Real timestomp artifact from the public EVTX-ATTACK-SAMPLES corpus (by sbousseaden),
# pulled from the shared dataset cache (lib/fetch.sh, source name evtx-attack-samples).
# Paths index into the cached clone, so they use real spaces (quoted at copy time).
# See PROVENANCE.md for dataset details and SHA-256 placeholders.
EVTX_FILES := \
	"Defense Evasion/sysmon_2_11_evasion_timestomp_MACE.evtx"

fetch-data:  ## Download the real timestomp EVTX sample into data/ (idempotent)
	@mkdir -p data
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
	repo=$$(fetch_repo evtx-attack-samples); \
	for f in $(EVTX_FILES); do \
		out="data/$$(basename "$$f")"; \
		if [ -f "$$out" ]; then \
			echo "exists: $$out"; \
		else \
			echo "fetch:  $$out"; \
			cp "$$repo/$$f" "$$out"; \
		fi; \
	done
	@echo "Done. Verify SHA-256 against PROVENANCE.md, then run 'make demo'."

up:
	docker compose up -d --build
	@echo "Container ready."
	@if [ ! -f data/disk.img ]; then \
		echo "disk.img not found — generating inside container..."; \
		docker compose exec lab python3 /scripts/create_ext2_img.py /data/disk.img; \
	fi
	@echo "Run 'make demo' to analyse the disk image."

create-image:
	docker compose exec lab python3 /scripts/create_ext2_img.py /data/disk.img

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	docker compose exec lab sh /scripts/demo.sh

shell:
	docker compose exec lab bash
