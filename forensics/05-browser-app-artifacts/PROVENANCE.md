# Provenance — Lab 05 Browser & Application Artifacts data

## Primary real dataset: Nitroba University Harassment scenario (Digital Corpora)

- **Dataset:** "Nitroba University Harassment Scenario" — a public DFIR teaching scenario built
  around a real packet capture. Chemistry instructor *Lily Tuckrige* receives harassing emails;
  investigators sniff dorm network traffic to identify the student who sent them, reconstructing the
  suspect's **webmail sessions and browser/user-agent artifacts** from the capture.
- **Author / source:** Digital Corpora (Simson Garfinkel et al.).
  PCAP: https://downloads.digitalcorpora.org/corpora/scenarios/2008-nitroba/nitroba.pcap (~60MB)
  Scenario landing: https://digitalcorpora.org/corpora/scenarios/nitroba-university-harassment-scenario/
- **License / status:** published by Digital Corpora for forensic education and research; freely
  fetchable. Use for training/education.
- **How it is used here:** the Nitroba PCAP is the **real artifact** — the suspect's webmail
  activity and browser artifacts (HTTP webmail sessions, User-Agent strings) are reconstructed from
  the capture. `make fetch-data` downloads it into `data/nitroba.pcap`. The bundled
  `data/History` (Chrome SQLite) is retained as the **offline demo seed** so `make demo` runs before
  `fetch-data`; it is modelled on the Nitroba scenario with neutral naming (account `jsmith`,
  anonymizer/webmail domains `willselfdestruct.com`, `sendanonymousemail.net`), replacing the prior
  synthetic browsing seed.

### File wired

| Purpose | File | URL |
|---|---|---|
| Real webmail/browser-artifact reconstruction | `nitroba.pcap` | https://downloads.digitalcorpora.org/corpora/scenarios/2008-nitroba/nitroba.pcap |

### SHA-256 (fill after fetch)

Run `sha256sum data/nitroba.pcap` after `make fetch-data` and record here to pin the artifact:

```
<fill after fetch>  nitroba.pcap
```

> Fetch and SHA-256 validation are **deferred to runner-validation** — the download has not been
> executed in authoring.

## Demo seed (retained)

- `data/History` — small Chrome `History` SQLite DB (urls / visits / downloads /
  keyword_search_terms), built to model the Nitroba webmail-harassment timeline (window
  2024-03-15 02:00–02:35 UTC) with neutral naming. Offline fallback so `make demo` runs before
  `fetch-data`. It replaces the prior synthetic seed.
