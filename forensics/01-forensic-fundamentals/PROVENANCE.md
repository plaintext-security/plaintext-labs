# Data provenance — Lab 01 (Forensic Fundamentals)

## Primary artifact: Digital Corpora — M57-Patents scenario

- **Dataset name:** M57-Patents Scenario (Garfinkel, Farrell, Roussev, Dinolt)
- **Canonical URL (root):** https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/
- **USB images subpath (used by this lab):** https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/
- **What it is:** Real, publicly distributed forensic disk/USB/RAM/network images covering the
  first four weeks (Nov 13–Dec 12 2009) of the fictional-but-real M57 Patents company, an
  outsourced patent-search firm. Investigations in the scenario include data exfiltration and
  illegal activity. Lab 01 uses a **USB image** from the `/usb/` subpath as the evidence to hash
  and chain-of-custody.
- **License / terms:** Digital Corpora material is freely available for research and education
  (digitalcorpora.org). No charge; cite the corpus and Garfinkel et al.
- **SHA-256:** _fill after fetch_ — run `make fetch-data`, then `sha256sum data/m57-usb.*` and
  record the value here as the integrity baseline.

## Narrative anchor

The lab's *story* is The DFIR Report's **"From a Single Click: How Lunar Spider Enabled a Near
Two-Month Intrusion"** (2025-09-29). M57 supplies the real bytes; Lunar Spider supplies the real
intrusion chain (`Form_W-9.js` → `update.msi` → Latrodectus → Rclone/`sihosts.exe` exfiltration).

## Replaces

This replaces the prior **synthetic financial-org seed**. The bundled
`data/evidence-sample.txt` / `data/evidence-sample.bin` are retained only as a tiny **offline
fallback** so `make demo` runs with no network; the M57 image is the primary artifact.

> Fetch + SHA-256 validation are deferred to runner-validation; `make fetch-data` is wired but not
> yet executed in-repo.
