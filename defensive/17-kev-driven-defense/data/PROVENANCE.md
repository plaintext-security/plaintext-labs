# Data provenance — KEV-Driven Defense

This lab is built on real, citable artifacts. The bundled `data/` is a small,
committed **snapshot** so `make demo` runs fully offline and deterministically;
the live feeds and exploit target are pulled on demand.

## `kev_snapshot.json` — CISA KEV catalog snapshot

- **Source:** CISA Known Exploited Vulnerabilities (KEV) Catalog.
- **Verified URL (live JSON):** https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
- **Catalog page:** https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **License / usage:** CISA KEV is U.S. Government work, free to use and redistribute.
- **Contents:** a committed snapshot of the KEV catalog (the most-recent entries
  plus every entry that maps to a runnable Vulhub target). Reframed as a snapshot —
  it ages. Run `make refresh` to diff it against **today's** live catalog.
- **Fetch pipeline (deferred — not executed here):** `make refresh`
  (`kev_refresh.py --live`) GETs the live JSON above.

## `solr_access.log` — Apache Solr access log (Log4Shell)

- **Shape:** a real Apache Combined Log Format access log for Apache Solr 8.11.0,
  containing benign admin/query traffic and three Log4Shell (CVE-2021-44228) JNDI
  exploit attempts in the URI, a header, and the User-Agent.
- **Reference CVE:** CVE-2021-44228 — KEV-listed, ransomware-flagged.
  - NVD: https://nvd.nist.gov/vuln/detail/CVE-2021-44228
- **Reproducible target:** Vulhub CVE-2021-44228 (Apache Solr) —
  https://github.com/vulhub/vulhub/tree/master/log4j/CVE-2021-44228
  Stand it up with `make target-up`; it is never committed.
- **Usage:** seed log committed on purpose so the detection step has data offline.

## `vulhub_catalog.json` — KEV → Vulhub target map

- **Source:** hand-curated mapping of KEV CVE IDs to Vulhub environments.
- **Vulhub:** https://github.com/vulhub/vulhub (Apache-2.0).
- **Contents:** CVE → Vulhub path entries used to flag which KEV entries are runnable.

## Citation

> CISA, "Known Exploited Vulnerabilities Catalog." Apache Software Foundation,
> "Apache Solr." Vulhub, "CVE-2021-44228 (Apache Solr)." Apache Log4j2
> CVE-2021-44228.
