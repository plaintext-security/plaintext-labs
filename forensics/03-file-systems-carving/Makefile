# Module 03 — File Systems & Carving lab.
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell fetch-data

# --- Real evidence: Digital Corpora M57-Patents -------------------------------
# Downloads a real, freely licensed M57 USB image into data/ for carving practice
# (idempotent). See PROVENANCE.md. Not executed in-repo — deferred to runner-validation.
M57_USB_URL := https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/
fetch-data:  ## Download a real M57-Patents USB image into data/ (idempotent)
	@mkdir -p data
	@if [ -f data/m57-usb.aff ] || [ -f data/m57-usb.E01 ] || [ -f data/m57-usb.raw ]; then \
		echo "M57 image already present in data/ — skipping download."; \
	else \
		echo "Fetching the smallest M57 USB image from $(M57_USB_URL)"; \
		echo "(Pick a specific file from the index above; example:"; \
		echo "  curl -fL -o data/m57-usb.raw $(M57_USB_URL)<image-name>.raw )"; \
		echo "Then run 'fls -r -d data/m57-usb.* ' and carve with foremost."; \
	fi

up:  ## Build and start the SleuthKit + foremost container
	docker compose up -d --build

down:  ## Stop and remove the container
	docker compose down

reset:  ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:  ## Open a shell in the lab container
	docker compose exec lab bash

demo:  ## Worked example: parse disk.img, list deleted files, recover content, carve
	docker compose run --rm lab sh -c '\
		echo "=== Module 03 — File Systems & Carving: worked demo ==="; \
		echo; \
		echo "-- Step 1: Filesystem summary (fsstat) --"; \
		fsstat data/disk.img 2>&1 | head -30; \
		echo; \
		echo "-- Step 2: All files including deleted (fls -r -d) --"; \
		fls -r -d data/disk.img 2>&1; \
		echo; \
		echo "-- Step 3: Recover the deleted file via icat --"; \
		echo "(Deleted file is at inode 4 in this FAT32 image)"; \
		icat data/disk.img 4 2>/dev/null | cat; \
		echo; \
		echo "-- Step 4: Carve unallocated space with foremost --"; \
		mkdir -p /tmp/foremost-out; \
		foremost -t all -i data/disk.img -o /tmp/foremost-out/ 2>&1; \
		echo; \
		echo "-- foremost audit summary --"; \
		cat /tmp/foremost-out/audit.txt 2>/dev/null || echo "(no audit.txt — check foremost output)"; \
		echo; \
		echo "=== Demo complete. The deleted EXFIL.TXT content should appear above. ==="'
