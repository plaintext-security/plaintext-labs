# Validation — Module 12 (Config & Posture Drift)

> **Status: SCAFFOLDED, NOT YET RUN.** Authored without a Docker daemon available.
> Run the command below on a Linux runner (Docker installed) to validate, then add
> a `.ci-demo` marker once green — see the CI note in `lab.md`.

## Prerequisites
- Docker + Docker Compose v2 (`docker compose`, not `docker-compose`).
- Linux host (the container is `privileged: true` for sysctl writes; sysctl
  changes inside a container affect the namespace where supported — on a Linux
  runner the `--check --diff` detection of the on-disk drift still works
  regardless, since the detector reads the declared playbook against on-disk
  config files). ~1 GB disk for the `ubuntu:22.04` + Ansible image.
- No cloud credentials, no cost.

## Validate
```bash
cd plaintext-labs/endpoint-hardening/12-config-drift
make up && make demo && make down
```

## What `make demo` proves
1. **Baseline (t=0):** `drift-loop.sh detect` reports zero drift — observed == declared.
2. **Inject drift:** `drift.sh inject` flips `rp_filter` (CIS-3.3.7), re-opens
   `PermitRootLogin` (CIS-5.2.10), drops a world-writable file (CIS-6.1.10).
3. **Detect:** a **control-named delta** for all three (control ID + before→after),
   not a score; the detector **fails closed** on a verify error and **exits non-zero**
   when drift is found.
4. **Loop:** alerts on the delta **first** (structured drift-event records to
   `drift-events.log`), **then** reconciles back to baseline.
5. **Detect again:** a clean host is **silent** (delta-only, no false alarm).

## Likely first-run fixups (no daemon was available to confirm)
- `sysctl -w` may be restricted in the container even with `privileged: true` on
  some kernels; the `drift.sh` writes are wrapped in `|| true` and the detector
  keys off the on-disk `99-cis-hardening.conf` value, so detection still
  fires. If a runner blocks the runtime write entirely, only the live-value side
  effect is skipped — the file-level drift/diff path is unaffected.
- The `--check --diff` output format is what `parse_delta` keys on; if Ansible
  9.4.0's diff layout differs from expectations, adjust the awk in
  `data/drift-loop.sh`. The control IDs are carried in the playbook task names,
  so the mapping is stable.
- `osquery` is optional (`data/drift-queries.sql`); it is **not** installed in the
  image and is provided as the cross-check queries only.

## Files
- `Dockerfile`, `docker-compose.yml`, `Makefile`
- `data/playbook.yml` — declared baseline (Module-06 controls + rp_filter + world-writable check)
- `data/drift.sh` — drift injection (`inject` / `undo`)
- `data/drift-loop.sh` — detector + control-named diff + reconcile + alert (fails closed, exits non-zero on drift)
- `data/drift-queries.sql` — optional osquery cross-check
- `data/drift-loop.cron` — schedule wiring
