# Data provenance — Module 15, Work Real Threat Intel

This lab enriches indicators against a **real abuse.ch ThreatFox feed**. The bundled
`data/` is a small committed snapshot so `make demo` runs fully offline and
deterministically; the live feed is pulled on demand with `make fetch-data`.

## `threatfox_sample.csv` — committed ThreatFox-format snapshot (the seed)

- **Schema:** the exact ThreatFox bulk-export CSV columns —
  `first_seen_utc, ioc_id, ioc_value, ioc_type, threat_type, fk_malware,
  malware_alias, malware_printable, last_seen_utc, confidence_level, reference,
  reporter`.
- **Contents:** a handful of illustrative IOCs in the real schema (Cobalt Strike
  `ip:port` C2, an AsyncRAT/RedLine sample, a phishing URL) using neutral/`.invalid`
  placeholder values so the demo never alerts on a third party. It is a *format-true*
  seed, not a copy of the live catalog.
- **Why it ships:** `enrich.py` falls back to this snapshot when no live feed is
  present, so the lab teaches the parser + Pyramid-of-Pain reasoning with zero
  network access.

## The real artifact (`make fetch-data`)

The real exercise enriches against **today's** live IOCs from **abuse.ch ThreatFox**,
the community IOC database for malware C2 and payload-delivery infrastructure.

- **Project:** abuse.ch ThreatFox — https://threatfox.abuse.ch/
- **Verified live CSV export (recent IOCs):**
  https://threatfox.abuse.ch/export/csv/recent/ — same column schema as the seed, so
  the same `enrich.py` parser works against either file.
- **Bulk-export index:** https://threatfox.abuse.ch/export/
- **API (for the Automate & own it step):** `https://threatfox-api.abuse.ch/api/v1/`
  — POST `{"query": "search_ioc", "search_term": "<ioc>", "exact_match": true}`
  with an `Auth-Key` header (free key from the abuse.ch auth portal).
  Docs: https://threatfox.abuse.ch/api/
- **License / usage:** abuse.ch datasets are free for non-commercial use under the
  abuse.ch terms; do not redistribute the bulk feed — fetch it from source.

## Fetch pipeline

`make fetch-data` GETs the live CSV above to `data/threatfox_recent.csv` (gitignored).
`enrich.py` then prefers that live snapshot and only falls back to the committed
`threatfox_sample.csv` if it is absent. NOT run in CI — you run it locally.

## One-line citation

> abuse.ch, "ThreatFox" (IOC database), recent-export CSV
> https://threatfox.abuse.ch/export/csv/recent/ and API
> https://threatfox-api.abuse.ch/api/v1/.
