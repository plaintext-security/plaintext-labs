# Validation — Module 13 (Fleet Migration)

> **Status: SCAFFOLDED, NOT YET RUN.** Authored without a Docker daemon available.
> Run the command below on a Linux runner (Docker installed) to validate, then add
> a `.ci-demo` marker once green — see the CI note in `lab.md`.

## Prerequisites
- Docker + Docker Compose v2 (`docker compose`).
- Linux host. ~1 GB disk for `ubuntu:22.04` + Ansible. No cloud credentials, no cost.
- The fleet model runs entirely inside the one container (per-host state dirs +
  tiny Python HTTP `/health` servers on `127.0.0.1:1800N`); no inter-container
  SSH and no external ports are required.

## Validate
```bash
cd plaintext-labs/endpoint-hardening/13-fleet-migration
make up && make demo && make down
```

## What `make demo` proves
1. **Starting state:** all 6 hosts serve `/health` (200) **before** any hardening.
2. **Test ring:** host-01 rolled — **hardened AND still serving**; rest untouched.
3. **Canary under full baseline:** the **legacy host (host-05) breaks** (503) — the
   after-health gate **fails** and the rollout **halts** (failure % > `max_fail`),
   rest of fleet untouched. This is the predicted compliant-but-down failure.
4. **Defended exception:** re-roll canary with `EXC=1` → legacy host gets the
   **relaxed profile** (umask 022) and is healthy; other canary hosts at full baseline.
5. **Per-ring rollback:** `rollback RING=canary` re-converges to serving-the-old-way,
   then re-roll — a rollback you actually run.
6. **Fleet ring:** rolled in batches (`serial=2`, `max_fail=25%`) with the per-batch
   health gate.
7. **Final proof:** `fleet-health.sh all yes` — every host hardened (or on its
   defended exception) **and** still serving; un-hardened surface is zero.

The health harness `fleet-health.sh` **fails closed**: a timeout / unreachable
endpoint (HTTP `000`) counts as a failure, never a silent pass.

## Design note (why a script, not pure-Ansible SSH)
To keep the demo deterministic and CI-runnable without fragile inter-container
SSH, the rollout is driven by `data/rollout.sh`, which implements the
rolling-upgrade pattern (serial batching, `max_fail_percentage` halt, pre/post
health gate). `data/playbook.yml` is the **production-shape Ansible expression of
the same pattern** (`serial`, `max_fail_percentage`, `pre_tasks`/`post_tasks`
health hooks, `group_vars/legacy-app.yml` exception) — the reference a learner
adapts for a real SSH-reachable fleet. Both express the identical ring/serial/
health-gate/exception discipline.

## Likely first-run fixups (no daemon was available to confirm)
- Confirm the Python `http.server` apps start and bind on `127.0.0.1:1800N`
  inside the container; `fleet.sh init` sleeps 1s before the first health check.
- The inventory parser (`awk` in `rollout.sh` / `fleet-health.sh`) strips inline
  `# comments`; verify ring membership prints correctly if you edit
  `data/inventory.ini`.
- Bash arrays are used (`#!/usr/bin/env bash`); the image's `/bin/bash` covers this.

## Files
- `Dockerfile`, `docker-compose.yml`, `Makefile`
- `fleet-health.sh` — service-health harness (serving + hardened-for-profile, fails closed)
- `data/fleet.sh` — fleet model (per-host state + HTTP health apps)
- `data/rollout.sh` — staged rollout (rings, serial, max_fail halt, health gate, exception, rollback)
- `data/playbook.yml` — the Ansible rolling-upgrade reference (serial / max_fail_percentage / health hooks)
- `data/inventory.ini` — fleet inventory grouped into test / canary / fleet / legacy-app rings
- `data/group_vars/all.yml`, `data/group_vars/legacy-app.yml` — full baseline + the relaxed-profile exception
