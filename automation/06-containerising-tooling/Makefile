.PHONY: up demo shell down reset scan seed clean-seed

IMAGE = plaintext/trufflehog:1.0
SEED  = data/seed-repo

up: seed   ## Materialize the seed repo (clone it from the committed bundle)

seed: $(SEED)/.git  ## Reconstitute data/seed-repo/ from data/seed-repo.bundle
$(SEED)/.git:
	@echo ">> materializing seed repo from bundle"
	@rm -rf "$(SEED)"
	git clone -q data/seed-repo.bundle "$(SEED)"

demo: seed ## Build the image and run trufflehog against data/seed-repo/
	docker build -t $(IMAGE) .
	docker run --rm -v "$(PWD)/$(SEED):/scan:ro" $(IMAGE) \
		git file:///scan --no-update --no-verification

shell:     ## Shell inside the built container
	docker run --rm -it --entrypoint bash $(IMAGE)

down:      ## Remove the image
	docker image rm -f $(IMAGE) 2>/dev/null || true

clean-seed:  ## Remove the materialized seed repo (keeps the bundle)
	rm -rf "$(SEED)"

reset: down clean-seed

scan:      ## make scan DIR=/path/to/repo — scan an arbitrary repo
	docker run --rm -v "$(DIR):/scan:ro" $(IMAGE) \
		git file:///scan --no-update --no-verification
