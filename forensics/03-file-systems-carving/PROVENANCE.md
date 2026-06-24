# Data provenance — Lab 03 (File Systems & Carving)

## Primary artifact: Digital Corpora — M57-Patents scenario

- **Dataset name:** M57-Patents Scenario (Garfinkel, Farrell, Roussev, Dinolt)
- **Canonical URL (root):** https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/
- **USB images subpath (used by this lab):** https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/
- **Redacted full-drive subpath (optional, larger):** https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/drives-redacted/
- **What it is:** Real, publicly distributed forensic images (drives, USB, RAM, network) from the
  first four weeks (Nov 13–Dec 12 2009) of the fictional-but-real M57 Patents company, an
  outsourced patent-search firm whose investigations include data exfiltration and illegal
  activity. Lab 03 uses a **USB image** from the `/usb/` subpath (smallest suitable) for
  `fsstat` / `fls` / `icat` / `foremost` carving; the `/drives-redacted/` images offer a richer,
  larger carving target.
- **License / terms:** Digital Corpora material is freely available for research and education
  (digitalcorpora.org). No charge; cite the corpus and Garfinkel et al.
- **SHA-256:** _fill after fetch_ — run `make fetch-data`, then `sha256sum data/m57-usb.*` and
  record the value here as the chain-of-custody baseline (carried from Lab 01).

## Narrative anchor

The lab's *story* is The DFIR Report's **"From a Single Click: How Lunar Spider Enabled a Near
Two-Month Intrusion"** (2025-09-29) — `Form_W-9.js` → `update.msi` → Latrodectus → Rclone
(`sihosts.exe`) exfiltration. M57 supplies the real bytes to carve.

## Replaces

This replaces the prior **synthetic "Meridian" FAT32 seed**. The committed `data/disk.img` (2MB
FAT32 with a planted deleted file) is retained only as an offline **fallback** so `make demo` runs
with no network. The M57 USB image is the primary artifact.

> Fetch + SHA-256 validation are deferred to runner-validation; `make fetch-data` is wired but not
> yet executed in-repo.
