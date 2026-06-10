# Module 08 — Patch & Vulnerability Management

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 07 — Endpoint & Host Hardening]** — *Hardening reduces the attack surface of the software you need; patch management eliminates the vulnerabilities in it.*

## Why this matters

Unpatched vulnerabilities in known-exploited software are the leading cause of breaches. The CISA Known Exploited Vulnerabilities catalogue lists hundreds of CVEs that adversaries are actively exploiting — the vast majority of which had patches available before they appeared in incident reports. Vulnerability management is the operational discipline that closes this gap: knowing what software is installed, which CVEs apply to it, and in what order to patch based on actual exploitation evidence rather than CVSS scores alone.

## Objective

Use osquery to enumerate installed packages and versions on a Linux host, scan with grype for CVEs, cross-reference the findings to identify the highest-priority patches, and produce a prioritised remediation list — the same workflow a vulnerability management programme runs in production.

## The core idea

Vulnerability management fails in one of two ways: organisations either patch nothing because the queue is overwhelming, or they patch everything indiscriminately and spend engineering cycles on theoretical vulnerabilities while real ones accumulate. The solution is a triage model that combines vulnerability severity with exploitation evidence. CVSS alone is not sufficient — a CVSS 9.8 vulnerability in an application that is not exposed or not reachable from the network is lower priority than a CVSS 6.5 vulnerability in an internet-facing service that appears in CISA's KEV catalogue. The discipline is building and applying that triage model consistently.

osquery's role in vulnerability management is asset inventory: it knows exactly what is installed on each host (package names, versions, paths), when packages were last updated, and what processes are running. This is the "what do we have" question. grype is the scanner that answers "what CVEs apply to what we have" — it compares the package inventory against the NVD (National Vulnerability Database), GitHub Advisory Database, and other vulnerability feeds and produces a finding list with CVE IDs, severity ratings, and the fixed version that closes each finding. Together, osquery (inventory) and grype (CVE matching) replace the expensive commercial vulnerability scanner for most endpoint use cases.

The prioritisation step is where most organisations lose the signal. A raw grype output against a modern Ubuntu system will produce dozens or hundreds of findings. Sorting by CVSS score alone produces a list where network-unreachable memory-corruption vulnerabilities outrank actively-exploited authentication bypass bugs. The correct prioritisation combines: is the CVE in CISA's KEV catalogue (active exploitation evidence), is the service exposed (network reachability), is a patch available (fix exists), and what is the software's role (SUID binary exploited locally is different from unexposed library). This triage model turns hundreds of findings into a single-page remediation priority list.

Patch management and vulnerability scanning are often separated in organisations, with different teams owning each. The security engineer's role is to bridge the gap: produce the prioritised finding list, translate it into the terms the operations team understands (package name and `apt upgrade` command, not CVE ID and CVSS vector), and track closure rates over time. A vulnerability that stays open for 30 days after a patch is available is a governance failure, not just an engineering gap — the management discipline is as important as the technical one.

## Learn (~3 hrs)

**Vulnerability management frameworks**
- [CISA Known Exploited Vulnerabilities Catalogue](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) — the authoritative list of CVEs with confirmed exploitation in the wild; understand how to query it and why KEV membership changes prioritisation.
- [NIST NVD — Understanding CVSS v3](https://nvd.nist.gov/vuln-metrics/cvss) — read the scoring guide for the Environmental and Temporal metrics; understand why a base CVSS score alone is insufficient for prioritisation.

**Scanning tools**
- [grype documentation (Anchore)](https://github.com/anchore/grype) — read the README and the "Supported ecosystems" section; understand what package types it can scan and what vulnerability feeds it uses.
- [Syft — SBOM generation (Anchore)](https://github.com/anchore/syft) — grype's companion tool that generates a Software Bill of Materials; understand how the SBOM feeds the CVE scan.

**osquery for vulnerability management (revisit from module 05)**
- [osquery deb_packages table](https://osquery.readthedocs.io/en/stable/introduction/sql/) — the schema for querying installed packages on Debian/Ubuntu systems; note `version` and `source` columns.

**Patch management at scale**
- [NIST SP 800-40 r4 — Guide to Enterprise Patch Management Planning](https://csrc.nist.gov/pubs/sp/800/40/r4/final) — Sections 1–3; the framework for building a patch management programme with SLAs.

## Key concepts

- CVSS base score alone is insufficient; prioritise by KEV membership (active exploitation), patch availability, and service exposure.
- osquery = inventory ("what is installed"); grype = CVE matching ("what vulnerabilities apply").
- An SBOM (Software Bill of Materials) from Syft feeds grype without requiring a running host scan.
- Vulnerability management SLAs: Critical/KEV ≤ 7 days; High ≤ 30 days; Medium ≤ 90 days (CISA guidance baseline).
- Track closure rates — a finding that stays open 90 days past SLA is a governance issue.

## AI acceleration

Paste a grype finding (CVE ID + package name + version) into an AI and ask it to explain: what the vulnerability is, what the exploit scenario looks like, whether a patch is available, and whether you've seen it in CISA KEV. Use the explanation to write the triage rationale entry in your remediation list. AI accelerates the "what is this CVE" research; you verify against NVD and KEV before assigning priority.
