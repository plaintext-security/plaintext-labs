# Lab 04 — HTTP & APIs for Enrichment

*Hands-on lab · [← Back to the module concept](README.md)*

> **Lab environment: real-feed rewire — validation deferred.** The threat-intel API now serves
> real abuse.ch data (Feodo Tracker + URLhaus) from `feeds/db.json` instead of synthetic verdicts.
> `make up && make demo && make refresh && make down` has **not** yet been re-run on a clean Linux
> runner against this change; validate before marking the lab done.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/04-http-apis-enrichment
make up        # starts the local threat-intel API + student container
make demo      # runs enrich.py against the API and shows enriched output
make refresh   # (optional, needs network) re-fetch the LIVE abuse.ch feeds into feeds/db.json
make shell     # interactive shell in the student container
make down
```

Two containers run: a **local threat-intel API** (Flask) on port 8080 that responds to
`GET /api/v3/ip/<ip>` and `GET /api/v3/hash/<sample_id>` with VirusTotal/AbuseIPDB-shaped JSON
— but the verdicts and IOCs are **real threat intelligence**, not invented. The API serves a
snapshot built from two free, no-key **abuse.ch** feeds:

- **[Feodo Tracker](https://feodotracker.abuse.ch/blocklist/)** — malicious botnet C2 IPs
  (Emotet / QakBot / Dridex), with ASN, country, and malware family.
- **[URLhaus](https://urlhaus.abuse.ch/api/)** — recently-reported malware-distribution URLs and
  samples, with threat tags and family.

The student container has `httpx`, `python-dotenv`, and `tenacity` installed.

**Provenance & offline fallback.** `feeds/db.json` is a committed snapshot of those live feeds;
every record carries a `source` (`abuse.ch Feodo Tracker` / `abuse.ch URLhaus`) and a
`fetched_at` timestamp so the data's origin is auditable. The lab runs fully offline against the
snapshot. To pull fresh IOCs, run `make refresh` (it executes `feeds/fetch_feeds.py` against the
live feeds, with network) and re-run the demo against today's real data. Hit
`GET /api/v3/meta` to see exactly which sources and snapshot date you're enriching against.

`data/iocs.txt` contains 20 IOCs — real malicious C2 IPs and URLhaus sample ids from the
snapshot, three known-clean public resolvers (8.8.8.8 / 1.1.1.1 / 9.9.9.9), one
not-in-feed IP (404), and one malformed line. For two of the real malicious IPs the API returns
`429` once before succeeding, to force retry handling.

> Everything runs locally against a real-IOC snapshot. No API keys required (the dummy key
> exercises the auth pattern). `make refresh` is the only step that reaches the internet.

## Scenario
Your SOC's SIEM raised 20 IOCs in the last hour. You need to enrich each one against your
threat-intel API — here, real abuse.ch data served locally — and produce a report: which IOCs
are malicious, which are clean, which are unknown, and which timed out. The lead wants the
enriched data in JSON for automated downstream processing.

## Do
1. [ ] Read the API source in `mock-api/app.py` and the data it serves in `feeds/db.json` to
   understand what each endpoint returns (status codes, real verdicts, provenance fields) and which
   real IPs are 429'd. Don't run the reference yet — you'll use it as a check at the end.
2. [ ] Write your own `enrich.py` using `httpx.Client`:
   - Load the (dummy) API key from `os.environ.get("VT_API_KEY", "demo-key")`.
   - Set a `timeout=httpx.Timeout(connect=5.0, read=10.0)` on the client.
   - Iterate over `data/iocs.txt` line by line.
   - For each IOC, detect type (IP vs URLhaus sample id), call the correct endpoint.
   - Accumulate results in a list of dicts, keeping the `source`/`fetched_at` provenance fields.
3. [ ] Handle each HTTP status:
   - `200`: parse and store the result.
   - `404`: mark as "unknown" and continue.
   - `429`: sleep 2 s and retry once. If it fails again, mark as "rate-limited".
   - `500`/`503`: mark as "error" and continue.
4. [ ] Write the accumulated results to `output/enriched.json` using `json.dump`.
5. [ ] Print a terminal summary: counts of malicious / clean / unknown / error.
6. [ ] **Prove it with a test you wrote (the ownership half).** Don't stop at "my output looks like
   the reference." Write `test_enrich.py` that imports your enrichment function and asserts its
   behaviour against the deterministic mock API:
   - The two IOCs that return `429` once **succeed on retry** — their result is the underlying
     verdict, not `rate-limited`.
   - A known-malicious IOC returns `verdict == "malicious"` and a known-clean IOC returns
     `verdict == "clean"` (read `feeds/db.json` to pick concrete real IOCs, e.g. a Feodo C2 IP
     vs `8.8.8.8`).
   - A 404 IOC returns `verdict == "unknown"` and does not raise.

   Have a model draft the tests; read every assert; run them with `python -m pytest test_enrich.py`
   and confirm green. This mirrors module 02's pos/neg `test_parser.py` — a committed test beats a
   reference diff because it survives leaving the lab.
7. [ ] Run `make demo` to compare your output against the reference `enrich.py`. Do the same IOCs
   come back malicious? Did you handle the retry (`429`) the same way? Where you differ, find out why.

## Success criteria — you're done when
- [ ] `enrich.py` processes all 20 IOCs without crashing.
- [ ] The two IOCs that trigger `429` are retried correctly and succeed on the second attempt.
- [ ] `output/enriched.json` exists with 20 entries, each having an `ioc`, `type`, and `verdict` field.
- [ ] The terminal summary prints accurate counts.
- [ ] `test_enrich.py` asserts the `429`-retry success and the malicious/clean/404 verdicts, and
  passes under `python -m pytest test_enrich.py`.

## Deliverables
`enrich.py` + `test_enrich.py`. Commit both; add `output/` to `.gitignore` (commit `enriched.json`
only if you want the sample run in the portfolio).

## Automate & own it
**Required.** Wrap the enrichment loop in a `enrich_batch(iocs: list[str], max_workers: int = 5)
-> list[dict]` function and add a `--concurrency` CLI flag. Have a model draft the
`concurrent.futures.ThreadPoolExecutor` version; review the thread safety of the results list
(does it need a lock?). Commit the concurrent version as `enrich_async.py`.

## AI acceleration
Describe the retry logic to a model and ask it to implement it using `tenacity`. Then read every
decorator argument: what does `stop=stop_after_attempt(3)` do? What happens on the fourth
failure? Is `wait=wait_exponential(multiplier=1, max=10)` the right back-off for a `429`?
Understanding each argument is the review step.

## Connects forward
This enrichment function becomes the engine of the CLI tool in module 05 and the MCP server in
module 09. In Track 10 (Security Automation), module 07 wraps this into a scheduled pipeline.

## Marketable proof
> "I enrich IOCs programmatically against threat-intel APIs — with proper auth, timeouts, retry
> logic for rate-limiting, and structured JSON output — not copy-paste into a browser."

## Stretch
- Add `--output-format csv` to write the enriched results as a CSV for the ticket system.
- Implement proper exponential backoff with jitter for 5xx errors using `tenacity`.
