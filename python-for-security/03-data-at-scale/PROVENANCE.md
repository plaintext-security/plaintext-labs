# Corpus provenance — `data/eve.json`

`data/eve.json` is **real Suricata output**, not synthetic. It is committed as a small curated seed so the
lab is self-contained; regenerate it with `make gen` (see `gen_eve.sh`).

| Field | Value |
|---|---|
| Source PCAP | Malware-Traffic-Analysis.net — 2024-07-30, "Traffic analysis exercise: You dirty rat!" (STRRAT RAT infection) |
| PCAP URL | https://www.malware-traffic-analysis.net/2024/07/30/2024-07-30-traffic-analysis-exercise.pcap.zip |
| PCAP sha256 | `420530cefb5f0001e12aacc554cef14f6273f1e2ec01008567a68f3471e0ed70` (10,750,172 bytes) |
| Zip password | `infected_20240730` (MTA scheme: `infected_YYYYMMDD`) |
| Generator | Suricata 8.0.6 RELEASE (`jasonish/suricata:latest`) |
| Ruleset | Emerging Threats Open (`suricata-update`, default ET Open source) |
| Command | `suricata -r <pcap> -l <out> -k none` |

**The PCAP is fetched, never mirrored/committed** (MTA asks not to redistribute captures). The generated
`eve.json` is our derived artifact.

## Event mix (this capture)

`alert` 114 (102× **ET MALWARE STRRAT CnC Checkin**, C2 `141.98.10.79`), `flow` 199, `dns` 171, `smb` 130,
`dcerpc` 78, `tls` 65, `krb5` 56, `ldap` 46, `fileinfo` 6, `anomaly` 5, `http` 2, `mdns` 2, `stats` 1.

The demo replays this real corpus to demonstrate flat-memory streaming at scale; point `gen_eve.sh` at a
busier capture (`PCAP_URL=…`) for genuine hundreds-of-thousands volume.
