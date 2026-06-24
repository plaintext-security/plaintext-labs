# Data provenance — Module 06, SIEM Correlation

## What ships in this repo (the seed)

`events.json` is a **small curated seed** of 18 events, already normalized to the
harness's common schema, modelling two simultaneous incidents — an Office-macro
phishing chain on `WIN10-01` (encoded PowerShell → certutil download → Run-key
persistence → IDS hit) and an SSH brute-force success on `SRV-01`. It uses neutral
placeholder naming (`WIN10-01`, `CORP\user01`, `svc-backup`, RFC 1918 internal
hosts); it is illustrative, not a real capture. The seed exists so `make demo`
runs **fully offline** with no download.

## The real artifact (`make fetch-data`)

The seed is *already normalized*, which hides the ingest/normalize work a SIEM
actually does. To exercise that path on **genuine raw logs**, `make fetch-data`
pulls a real public sshd capture:

- **Dataset:** loghub `OpenSSH_2k.log` — ~2,000 real OpenSSH `sshd` auth lines
  captured on a host that was actively brute-forced (repeated `Failed password`,
  `Invalid user`, and `POSSIBLE BREAK-IN ATTEMPT` entries from many source IPs).
- **Source (verified):**
  https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log
- **Project:** loghub (https://github.com/logpai/loghub), a curated collection of
  system log datasets for log-analysis research.
- **License:** loghub datasets are released for research/educational use; see the
  loghub repository's terms. Do not redistribute the raw log from this repo —
  fetch it from the source.
- **Contains:** raw, unstructured sshd syslog lines — the natural input for the
  `rule_ssh_brute` / `rule_ssh_brute_success` correlation rules once normalized.

## Fetch + process pipeline

`make fetch-data` performs (and this file documents) the following — it is **not
run in CI; you run it locally**:

1. `curl -fL` the `OpenSSH_2k.log` from the URL above → `data/raw/OpenSSH_2k.log`.
2. Extend `normalize()` in `siem.py` to parse those raw sshd lines (timestamp,
   host, user, outcome, source IP) into the `events` table's schema.
3. Re-run `python3 siem.py` and confirm the SSH brute-force correlation rules fire
   on the real traffic, not just the curated seed.

Fetched logs (`data/raw/`, `*.log`) are gitignored (`data/.gitignore`); only the
curated `events.json` seed is committed.

## One-line citation

> loghub, "OpenSSH_2k.log" (sshd auth log sample),
> https://github.com/logpai/loghub. Normalized into the lab's SIEM schema.
