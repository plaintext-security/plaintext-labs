# Lab 08 — Patch & Vulnerability Management

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/08-patch-vuln-management
make up        # build the container with osquery, grype, and intentionally outdated packages
make demo      # run grype scan + osquery package query, show prioritised findings
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally. The container is built with a pinned set of older packages to ensure
> reproducible CVE findings.

## Scenario

Meridian Financial's security team has been asked to produce a monthly vulnerability report for
the payroll server fleet. The operations team manages 15 Ubuntu 22.04 servers and wants to know:
what CVEs exist, which to patch first, and what the patch command is. You will run the full
triage cycle on one host and produce a prioritised remediation list.

## Do

1. [ ] `make demo` — watch grype scan the container's packages and osquery enumerate installed
   packages. Note: the total CVE count, the number of Critical and High findings, and whether
   any appear in the CISA KEV catalogue.

2. [ ] `make shell` and run grype manually for JSON output:
   ```bash
   grype dir:/ --scope all-layers -o json > /tmp/grype-results.json
   # Count by severity:
   jq '.matches | group_by(.vulnerability.severity) | map({severity: .[0].vulnerability.severity, count: length})' \
     /tmp/grype-results.json
   ```

3. [ ] Run osquery to enumerate installed packages and compare with grype findings:
   ```bash
   osqueryi --json "SELECT name, version, arch FROM deb_packages ORDER BY name"
   ```
   Pick two packages that appear in both the osquery output and the grype findings. For each:
   note the installed version, the CVE ID, the fixed version, and the CVSS score.

4. [ ] Check the CISA KEV catalogue for the CVEs in your grype output:
   ```bash
   # Download the KEV catalogue (JSON):
   curl -s https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json \
     | jq '.vulnerabilities[].cveID' > /tmp/kev-ids.txt
   # Cross-reference:
   jq -r '.matches[].vulnerability.id' /tmp/grype-results.json | while read cve; do
     grep -q "$cve" /tmp/kev-ids.txt && echo "KEV: $cve"
   done
   ```
   Are any of your findings KEV-listed? If so, those are Priority 1.

5. [ ] Produce a prioritised remediation list in `remediation.md`. For the top five findings:
   - CVE ID and CVSS score
   - Affected package and installed version
   - Fixed version
   - KEV status (yes/no)
   - Priority (1=KEV or Critical, 2=High, 3=Medium)
   - Patch command: `apt-get install --only-upgrade <package>=<fixed-version>`

6. [ ] Simulate patching the highest-priority package:
   ```bash
   apt-get install --only-upgrade <package>
   ```
   Re-run grype and confirm the CVE count dropped.

## Success criteria — you're done when

- [ ] You have a grype JSON output with severity counts.
- [ ] You cross-referenced findings against CISA KEV.
- [ ] You produced a prioritised top-5 remediation list with patch commands.
- [ ] You patched one package and confirmed the CVE count dropped.

## Deliverables

`remediation.md` (your prioritised remediation list with triage rationale for each finding).
Commit it.

## Automate & own it

**Required.** Write a Python script `vuln-report.py` that reads `grype-results.json` and a
downloaded `known_exploited_vulnerabilities.json`, cross-references them, and outputs a
Markdown table sorted by: KEV first, then CVSS score descending. Have an AI draft the
cross-reference logic; you verify the sort order is correct and the KEV match is case-insensitive
before committing.

## AI acceleration

For each CVE in your top five, ask an AI: "What is CVE-XXXX-YYYY? What is the exploit scenario?
Is a patch available for Ubuntu 22.04?" Use the answer to write the "triage rationale" column
in your remediation list — one sentence explaining *why* this finding is at its assigned
priority. Verify the CVE description against NVD (`https://nvd.nist.gov/vuln/detail/CVE-XXXX-YYYY`)
before treating it as authoritative.

## Connects forward

The vulnerability inventory you build here feeds module 10 (detecting host compromise) — a host
running software with known CVEs is a detection priority. The patch management SLAs from
NIST SP 800-40 become governance metrics tracked in a compliance dashboard built in the track
capstone.

## Marketable proof

> "I scanned a Linux host with grype, cross-referenced CVEs against CISA KEV, and produced a
> prioritised remediation list with patch commands — the weekly output of a vulnerability
> management programme."

## Stretch

- Generate an SBOM with Syft first, then feed it to grype (`grype sbom:/tmp/sbom.json`). Compare
  the results to the direct directory scan — are there differences? The SBOM workflow is important
  for air-gapped environments where the scanner can't reach the host directly.
- Track the vulnerability count over time: run grype before and after patching several packages
  and plot the severity distribution. This is the "vulnerability debt" trend chart that
  security programmes use to show progress.
