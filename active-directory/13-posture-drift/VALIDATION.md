# Validation — Lab 13: AD Posture Drift & Steady-State

## What was built

A **deterministic simulation** of AD posture-drift detection: a committed hardened baseline,
an observed posture, a decay injector, and a detect->diff detector. No live Samba DC is
provisioned; the observed posture is a seed file mutated to simulate a month of decay, and
the detector diffs it against the declared baseline.

Files:
- `Dockerfile`, `docker-compose.yml`, `Makefile` — one-command environment (Debian + Python3 + cron + ldap-utils).
- `data/baseline.json` — the **declared hardened baseline** (the committed "this is good" posture + the krbtgt threshold with its M1015 justification). This file is the decision log: blessing a sanctioned change = editing it and committing who/why.
- `data/observed.json` — the observed posture (starts identical to baseline; mutated by the drift injector). `data/observed.clean.json` is the pristine reset source.
- `bin/drift-introduce.sh` — applies a realistic month of decay: new Kerberoastable SPN (`svc-newdb`), re-added `GenericWrite` ACE on `Finance-Managers`, `mnguyen` added to `Domain Admins`, krbtgt aged past threshold.
- `drift-detect.py` — **the deliverable**: the detect->diff->report loop. Strips comments, normalizes/sorts both sides, emits a **per-fact** delta (not a score) mapped to ATT&CK, exits non-zero on any drift. `--json` and `--out report.md` supported.

## Run it

```bash
cd plaintext-labs/active-directory/13-posture-drift
make up        # build the image, start the lab container
make demo      # t=0 clean (no drift) -> introduce drift -> detector names every regression
make down
```

`make detect` runs the detector once; `make drift` injects decay; `make reset-state`
restores the clean posture; `make schedule-example` prints a `crontab(5)` line for nightly
scheduling; `make shell` drops you in.

## Prerequisites

- Docker + Docker Compose v2 (`docker compose`).
- No internet at run time, no credentials, no external target.

## Verified

Scripts executed directly with the system `python3` (stdlib only — no third-party deps):
- Clean domain -> detector prints "NO DRIFT" and **exits 0** (no false positives).
- After `bin/drift-introduce.sh` -> detector names **all four** regressions as concrete
  facts (Kerberoastable `svc-newdb` -> T1558.003; `GenericWrite` on `Finance-Managers`
  -> T1098/T1484.001; `mnguyen` in `Domain Admins` -> T1098; krbtgt 211d > 180d -> T1558.001)
  and **exits 1**.
- Scoring-direction (the thing a model inverts) confirmed: krbtgt age `180` == threshold
  scores clean, `181` scores drift; an *absent* dangerous ACE / empty Kerberoastable list is
  **not** a finding; an *extra* privileged-group member is drift AND a *missing* expected
  member (e.g. `sgarcia` removed from `IT-Admins`) is also surfaced as drift.

Not run inside Docker here (Docker unavailable in the authoring environment), but the image
is a thin Debian + Python3/cron layer and the scripts are stdlib-only, so `make up && make
demo` on a clean Linux runner exercises the exact code paths verified above. **No `.ci-demo`
marker added** — add it only after `make up && make demo && make down` runs green on a Linux
runner.

## Gap to a full Samba-DC version (what a real DC would add)

This is a simulation by deliberate choice, matching Modules 09/10/12 in this track. A live
Samba-DC variant would replace the `observed.json` seed with **live collection** and add the
attack-graph corroboration step from `lab.md`, but the diff / report / exit logic — and the
human bless-or-enforce judgement the lab teaches — are unchanged. Specifically it would add:

1. **A live collector.** `drift-detect.py` already ships a `collect_observed_live(host)` sketch:
   ldap3 queries for SPN-bearing user objects (Kerberoastable), `userAccountControl` bit-AND
   filters (`0x400000` AS-REP, `0x80000` unconstrained delegation), privileged-group `member`
   reads, `nTSecurityDescriptor` parsing for non-default ACEs, and `pwdLastSet` on `CN=krbtgt`
   for the age. It returns the same dict shape as `observed.json`, so the diff is reused verbatim.
   This needs the Module 02 Samba DC (`active-directory/02-enumeration/Dockerfile.dc`) wired in
   as a compose service (as Module 10 does) plus bind credentials.
2. **Real mutations.** `drift-introduce.sh` would call `samba-tool spn add`, `dacledit.py`,
   `samba-tool group addmembers`, and rotate/age the krbtgt against the live DC instead of
   editing JSON.
3. **Adalanche corroboration.** Run Adalanche (headless AD attack-graph analyzer) against the
   drifted DC to show the *graph* gains a privesc edge to Domain Admin that the t=0 graph
   lacked — the same delta seen as a reopened path, not just a changed attribute. Adalanche
   needs a live DC to ingest, which is why it is documented as the corroboration step rather
   than bundled here. (Reconciliation — rotating krbtgt twice per M1015, removing the ACE,
   ejecting the account — would likewise run against the live DC.)

The reason the reference AD labs simulate: Samba4 + a domain-joined Windows client is
VM/cloud-tier weight, and the *detection logic and adjudication judgement* — which is what
this module is actually about — are fully exercised by the deterministic fixtures.
