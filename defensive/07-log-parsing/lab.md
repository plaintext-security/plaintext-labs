# Lab 07 — Normalise a Real Messy Log

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/07-log-parsing
make up
make demo      # normalise the sample sshd log and print the parse rate (and the unparsed lines)
make down
```

The lab bundles a deliberately messy seed (`data/auth_sample.txt` — real-shaped sshd auth lines from a
bastion host, plus a CRON line and a corrupt line that *don't* fit the sshd pattern) and a stdlib
reference normaliser (`normalize.py`) that emits ECS-style events and reports the parse rate. That
harness is your **spec**: your job is to reproduce the same normalisation in **Vector (VRL)** — the
production tool — and match its output, then handle what it couldn't.

The seed keeps `make demo` offline. For the real exercise, `make fetch-data` pulls genuine public
logs — loghub `OpenSSH_2k.log` (~2k real sshd auth lines, actively brute-forced) and `Apache_2k.log`
(a second, *different* format) — so you normalise real messy logs at volume and across two shapes. See
`data/PROVENANCE.md`.

## Scenario
Turn an unstructured log into clean, normalised, queryable events — *without silently losing lines.*

## Do
1. [ ] `make demo` and read the output: **8 of 10** lines parse; the CRON line and the corrupt line do
   not. That 80% is the whole lesson — note exactly which lines fell through and why.
2. [ ] Inspect `data/auth_sample.txt`. How many distinct line shapes are there, and which fields
   identify an auth event (outcome, user, source IP, port)?
3. [ ] Reimplement the normalisation in **Vector VRL** (or grok): extract those fields and normalise to
   ECS names (`source.ip`, `user.name`, `event.outcome`, `event.action`) so your output matches the
   reference for the sshd lines.
4. [ ] Handle the unparsed lines *deliberately* — route them to a dead-letter stream rather than
   dropping them — and measure your parse rate the way the harness does.

## Success criteria — you're done when
- [ ] The raw log is emitted as structured, normalised events.
- [ ] Your field names follow a common schema.
- [ ] You know your parse rate and how failures are handled (not silently dropped).

## Deliverables
`parsing.md`: your parser config, the before/after of a line, your parse rate, and your failure
handling.

## AI acceleration
Have a model draft the grok/VRL parser — then **check the parse rate and spot-check fields against the
raw log**. A silently-dropped 5% is invisible until a detection misses; you own catching it.

## Connects forward
Normalised logs make detections (module 08) portable across sources — and they complete **Phase 1's
project**: a host + network telemetry pipeline with a real attack flowing through it.

## Marketable proof
> "I parse and normalise real, messy logs to a common schema (ECS) — measuring parse rate and
> handling failures — so detections work across every source."

## Automate & own it
**Required.** Your Vector/parser config *is* the artifact — commit it with a test that proves the
parse rate on the real log; have AI extend it to a second log format and review the diff.

## Stretch
- Add enrichment (geoIP on the source IP) and explain how that sharpens a later detection.

> **▶ Phase 1 project.** You've finished Phase 1 — now integrate these modules: [Phase 1 Project — Host + Network Telemetry Pipeline](../../phase-1-project.md).
