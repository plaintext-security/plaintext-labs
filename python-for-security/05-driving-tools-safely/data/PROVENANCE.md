# Corpus provenance — M05 data (two sensors, one capture)

Both sensors' logs are **real** and describe the **same** incident — regenerate with `make gen` (Suricata)
and `make gen-zeek` (Zeek). The PCAP is fetched + checksum-verified, **never mirrored/committed**.

| | Suricata (`data/eve.json`) | Zeek (`data/zeek/*.log`) |
|---|---|---|
| Format | EVE JSON (newline-delimited) | native TSV (`#fields`/`#types` header) |
| Posture | opinionated — **alerts** with ET signatures | descriptive — **facts** (connections, DNS, HTTP, TLS) |
| Generator | Suricata 8.0.6 + ET Open | Zeek 8.2.0 |

Shared source PCAP: Malware-Traffic-Analysis.net 2024-07-30 "You dirty rat!" (STRRAT RAT infection).
- URL: https://www.malware-traffic-analysis.net/2024/07/30/2024-07-30-traffic-analysis-exercise.pcap.zip
- sha256 `420530cefb5f0001e12aacc554cef14f6273f1e2ec01008567a68f3471e0ed70` (10,750,172 bytes)
- Zip password `infected_20240730` (MTA scheme `infected_YYYYMMDD`).

## The reconciliation the M05 stretch teaches

The STRRAT C2 `141.98.10.79` shows up in **both** views: Suricata fires `ET MALWARE STRRAT CnC Checkin`
on it; Zeek records the bare TCP connection to it in `conn.log` with no verdict. The RAT's recon
(`ip-api.com`) appears in Zeek `dns.log`/`http.log`. Same truth, two schemas — `sift`'s typed boundary
normalizes both into one domain model.

Committed Zeek sample: `conn.log`, `dns.log`, `http.log`, `ssl.log` (the four that mirror the EVE dissector
thread). Regenerate the full set (x509, files, kerberos, smb, …) with `make gen-zeek`.

## Third sensor — endpoint telemetry (Sysmon EVTX)

Host logs for the STRRAT capture don't exist publicly, so the endpoint beat is a **separate real incident**:
a Sysmon EventID 3 (network-connection) sample from Samir Bousseaden's **EVTX-ATTACK-SAMPLES**. It's the
*host* side — which **process** opened a connection to which IP — the view the network sensors can't get.

- Source: https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES — `Command and Control/DE_sysmon-3-rdp-tun.evtx`
- sha256 `1d1eb55d1b7c785db26e19b0d50b9eb4a7928671e4edeb82ea5182cb834c874a` (69,632 bytes)
- 73 records: 42× Sysmon EID 3 (network connection, `Image`→`DestinationIp`), 13× EID 1 (process create), …
- **GPL-licensed upstream — fetched, never mirrored/committed** (`*.evtx` is gitignored). `make gen-sysmon`
  fetches + checksum-verifies it; parse with `python-evtx`. It's a *different, non-JSON, non-TSV* format
  (binary EVTX → XML `EventData`), so it's the third distinct schema `sift`'s domain model must absorb.

