# Module 02 — Acquisition & Imaging lab.
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell fetch-data

# --- Real evidence: Digital Corpora M57-Patents -------------------------------
# Downloads a real, freely licensed M57 USB image into data/ for imaging practice
# (idempotent). See PROVENANCE.md. Not executed in-repo — deferred to runner-validation.
M57_USB_URL := https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/
fetch-data:  ## Download a real M57-Patents USB image into data/ (idempotent)
	@mkdir -p data
	@if [ -f data/m57-usb.aff ] || [ -f data/m57-usb.E01 ] || [ -f data/m57-usb.raw ]; then \
		echo "M57 image already present in data/ — skipping download."; \
	else \
		echo "Fetching the smallest M57 USB image from $(M57_USB_URL)"; \
		echo "(Pick a specific file from the index above; example:"; \
		echo "  curl -fL -o data/m57-usb.aff $(M57_USB_URL)<image-name>.aff )"; \
		echo "Then image it with 'dc3dd if=data/m57-usb.* of=... hash=sha256'."; \
	fi

up:  ## Build and start the dc3dd container
	docker compose up -d --build

down:  ## Stop and remove the container
	docker compose down

reset:  ## Tear down completely (container + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:  ## Open a shell in the lab container
	docker compose exec lab bash

demo:  ## Worked example: create 1MB source, image with dc3dd, verify hash
	docker compose run --rm lab sh -c '\
		echo "=== Module 02 — Acquisition & Imaging: worked demo ==="; \
		echo; \
		echo "-- Step 1: Create 1MB synthetic source device (random data) --"; \
		dd if=/dev/urandom of=/tmp/source.img bs=1M count=1 2>&1; \
		echo; \
		echo "-- Step 2: Image with dc3dd (SHA-256 inline) --"; \
		dc3dd if=/tmp/source.img of=/tmp/forensic-image.img hash=sha256 log=/tmp/acquisition.log 2>&1; \
		echo; \
		echo "-- Step 3: Acquisition log (inline hash proof) --"; \
		cat /tmp/acquisition.log; \
		echo; \
		echo "-- Step 4: Verify with sha256sum --"; \
		SRC=$$(sha256sum /tmp/source.img | cut -d" " -f1); \
		IMG=$$(sha256sum /tmp/forensic-image.img | cut -d" " -f1); \
		echo "Source hash : $$SRC"; \
		echo "Image hash  : $$IMG"; \
		if [ "$$SRC" = "$$IMG" ]; then \
			echo "RESULT: VERIFIED — source and image are identical"; \
		else \
			echo "RESULT: FAILED — hash mismatch, image is suspect"; \
		fi; \
		echo; \
		echo "=== Demo complete. ==="'
