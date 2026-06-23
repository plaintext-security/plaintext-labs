# Data provenance — 08-data-encoding artifacts

The point of this lab is decoding (not exploitation), so the artifacts are real-*shaped* encodings of
the exact kinds of data analysts decode daily, with all C2 indicators rendered un-resolvable.

## `data/artifacts.txt`

| Artifact | What it is | Real anchor |
|---|---|---|
| `PS_B64` | base64 PowerShell `-enc` download cradle | The genuine `powershell.exe -enc <base64>` loader pattern used by commodity malware — **Emotet** among them (the family named in the module README). `iex (New-Object Net.WebClient).DownloadString(...)` is the canonical cradle (ATT&CK [T1059.001](https://attack.mitre.org/techniques/T1059/001/) + [T1105](https://attack.mitre.org/techniques/T1105/)). |
| `URLENC` | URL-encoded `../../../etc/passwd` | Real path-traversal shape seen in web access logs. |
| `HEX` | hex-encoded C2 domain (`cdn-update.example`) | Bytes-as-text from a PE `.data` section; domain uses RFC 2606 `.example` so it never resolves. |
| `DOUBLE` | base64-over-URL-encoded cradle to `c2.cdn-update.invalid` | Layered-encoding peel; `.invalid` (RFC 2606) never resolves. |

These are inert encodings — **no malware, nothing to execute**. Fictional company naming has been
removed; the only "domains" are reserved-TLD placeholders that cannot exist.

## The live, real feed — CISA KEV (kept as-is)

Step 6 / `demo_kev_jq()` pulls the **live** CISA Known Exploited Vulnerabilities catalog:
<https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json>
This is a genuine, current, authoritative dataset (real CVE IDs, vendors, due dates) queried with
`jq`-equivalent logic — the lab's real-artifact anchor for "JSON is structure, not secrecy."

## RUNNER-VALIDATION NEEDED

- `make demo` decoding is offline and deterministic — should validate cleanly.
- `demo_kev_jq()` reaches `cisa.gov` over the network (not run in the authoring environment); validate
  on a runner with outbound access. The code already degrades gracefully if the feed is unreachable.
