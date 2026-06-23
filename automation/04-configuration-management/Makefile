.PHONY: up down reset shell demo harden drift-check inject-drift reconcile steady-state drift-detect idempotency-check

PLAY    = ansible-playbook -i data/inventory.ini data/hardening.yml
REFPLAY = ansible-playbook -i data/inventory.ini data/hardening-ref.yml

up:  ## Build, start, and provision the controller->target SSH key
	docker compose up -d --build
	@echo "Waiting for the target's sshd to accept connections (apt bootstrap)..."
	@for i in $$(seq 1 40); do \
		docker compose exec -T target bash -c 'test -f /run/sshd.pid || pgrep -x sshd >/dev/null' 2>/dev/null && break; \
		sleep 3; \
	done
	@echo "Generating ephemeral lab key + installing it on the target..."
	docker compose exec -T controller bash -c '\
		mkdir -p data/ssh && \
		[ -f data/ssh/lab_key ] || ssh-keygen -t ed25519 -N "" -C plaintext-lab-controller -f data/ssh/lab_key >/dev/null && \
		chmod 600 data/ssh/lab_key'
	docker compose exec -T controller bash -c 'cat data/ssh/lab_key.pub' | \
		docker compose exec -T target bash -c 'mkdir -p /root/.ssh && chmod 700 /root/.ssh && cat >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys'
	@echo "Ready. Try: make demo"

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec controller bash

harden:  ## Apply the declared baseline (enforcing run)
	docker compose exec controller bash -c '$(PLAY)'

drift-check:  ## Detect drift: dry run (--check --diff). 0 changed = steady-state
	docker compose exec controller bash -c '$(PLAY) --check --diff'

inject-drift:  ## Simulate an out-of-band manual change to the hardened host
	docker compose exec target bash -c \
		"sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
		 echo 'INJECTED: PasswordAuthentication set back to yes (out of band)'"

reconcile:  ## Re-enforce the baseline to correct detected drift
	docker compose exec controller bash -c '$(PLAY) --diff'

steady-state:  ## Assert the host is back on-spec (fails if any drift remains)
	docker compose exec controller bash -c \
		'out=$$($(PLAY) --check 2>&1); echo "$$out"; \
		 if echo "$$out" | grep -q "changed=[1-9]"; then \
		   echo "FAIL: host is NOT at steady-state — drift remains"; exit 1; \
		 else echo "PASS: steady-state confirmed (0 changed)"; fi'

drift-detect:  ## Run the committed drift detector against the reference role (detect-only; ARGS=--reconcile to self-heal)
	docker compose exec controller bash -c 'PLAYBOOK=data/hardening-ref.yml bash data/drift-detect.sh $(ARGS)'

demo:  ## Full drift loop (reference role): harden -> prove steady -> inject -> detect -> reconcile -> re-prove
	docker compose exec controller bash -c '\
		echo "=== Stage 1: harden (declare + apply baseline) ==="; $(REFPLAY); echo; \
		echo "=== Stage 2: drift-check — expect 0 changed (steady-state) ==="; $(REFPLAY) --check; echo'
	$(MAKE) inject-drift
	docker compose exec controller bash -c '\
		echo "=== Stage 4: drift-check after injection — expect non-zero changed ==="; $(REFPLAY) --check --diff; echo; \
		echo "=== Stage 5: reconcile — expect exactly 1 changed ==="; $(REFPLAY) --diff; echo; \
		echo "=== Stage 6: re-prove steady-state — expect 0 changed ==="; \
		out=$$($(REFPLAY) --check 2>&1); echo "$$out"; \
		if echo "$$out" | grep -q "changed=[1-9]"; then \
			echo "FAIL: drift remains after reconcile"; exit 1; \
		else echo "PASS: drift loop closed — steady-state reproven (0 changed)"; fi'

idempotency-check:  ## Back-compat: fail if a second enforcing run shows any changed tasks
	docker compose exec controller bash -c '\
		$(PLAY) && result=$$($(PLAY) 2>&1); echo "$$result"; \
		if echo "$$result" | grep -q "changed=[1-9]"; then \
			echo "FAIL: idempotency check failed — tasks changed on second run"; exit 1; \
		else \
			echo "PASS: idempotency confirmed — 0 changed on second run"; \
		fi'
