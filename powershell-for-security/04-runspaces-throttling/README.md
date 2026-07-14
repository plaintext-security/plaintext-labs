# Lab 04 — Enrichment with Runspaces & Throttling

Environment for **Track 13 · Module 04**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/04-runspaces-throttling/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer + Pester container
make shell   # drop into pwsh
make demo    # run the module gate (PSScriptAnalyzer + Pester) over the reference Vigil module
make down    # stop when done
```

- `Vigil/` — the **cumulative** reference module. It keeps `Get-VigilEvent` (from Module 01)
  and adds `Invoke-VigilEnrichment` — concurrent indicator enrichment with a throttle limit,
  retry/backoff, and thread-safe result collection.
- `data/feodo_ipblocklist.csv` — an **offline snapshot** of the abuse.ch Feodo Tracker IP
  blocklist (botnet C2 IPs). `make demo` enriches against this, never the network. Point
  `Invoke-VigilEnrichment -FeedPath` at a downloaded copy of the live feed to refresh.
- `data/events.json` — 10 Sysmon network-connection events (Event ID 3) carrying 9 unique
  destination IPs; 5 of them match the snapshot as malicious.
- `data/sample.json` — the Module 01 event export, kept so the cumulative `Get-VigilEvent`
  stays testable.

Everything runs offline and deterministic in the Linux container; zero cost.
