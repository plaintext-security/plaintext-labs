# Data provenance — Module 07, Log Parsing & Normalisation

## What ships in this repo (the seed)

`auth_sample.txt` is a **small curated seed** of 10 lines: 8 real-shaped sshd auth
lines from a bastion host plus a CRON line and a deliberately corrupt line that do
*not* fit the sshd pattern. It uses neutral placeholder naming (`bastion-01`, RFC
5737 documentation IPs like `203.0.113.9`). The 80% parse rate it produces is the
whole lesson — silent drops are where detections quietly miss. The seed exists so
`make demo` runs **fully offline** with no download.

## The real artifact (`make fetch-data`)

A 10-line seed can't show you parsing at volume or across formats. `make fetch-data`
pulls two genuine public logs, in **two different shapes**:

- **sshd:** loghub `OpenSSH_2k.log` — ~2,000 real OpenSSH auth lines captured on a
  host under active brute-force (`Failed password`, `Invalid user`,
  `POSSIBLE BREAK-IN ATTEMPT`).
  - Source (verified):
    https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log
- **Apache:** loghub `Apache_2k.log` — ~2,000 real Apache error-log lines
  (`[timestamp] [level] message`), a *different* format your parser must handle to
  prove the "normalise across every source" claim.
  - Source (verified):
    https://raw.githubusercontent.com/logpai/loghub/master/Apache/Apache_2k.log

- **Project:** loghub (https://github.com/logpai/loghub), a curated collection of
  system log datasets for log-analysis research.
- **License:** loghub datasets are released for research/educational use; see the
  loghub repository's terms. Do not redistribute the raw logs from this repo —
  fetch them from the source.

## Fetch + process pipeline

`make fetch-data` performs (and this file documents) the following — it is **not run
in CI; you run it locally**:

1. `curl -fL` `OpenSSH_2k.log` and `Apache_2k.log` → `data/raw/`.
2. Run your normaliser (and the reference `normalize.py`) over each, measuring the
   real parse rate and routing unparsed lines to a dead-letter stream rather than
   dropping them.
3. Confirm your Vector (VRL) config matches the reference on the sshd lines and
   *also* handles the Apache format — the second format is the portability proof.

Fetched logs (`data/raw/`, `*.log`) are gitignored (`data/.gitignore`); only the
curated `auth_sample.txt` seed is committed.

## One-line citation

> loghub, "OpenSSH_2k.log" and "Apache_2k.log" (system log samples),
> https://github.com/logpai/loghub.
