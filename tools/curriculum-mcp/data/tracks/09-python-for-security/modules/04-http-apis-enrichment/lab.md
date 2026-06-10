# Lab 04 — HTTP & APIs for Enrichment

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/04-http-apis-enrichment
make up        # starts the mock API server + student container
make demo      # runs enrich.py against the mock API and shows enriched output
make shell     # interactive shell in the student container
make down
```

Two containers run: a **mock API server** (Flask) on port 8080 that responds to
`GET /api/v3/ip/<ip>` and `GET /api/v3/hash/<hash>` with realistic VirusTotal/AbuseIPDB-shaped
JSON; and the **student container** with `httpx`, `python-dotenv`, and `tenacity` installed.

`data/iocs.txt` contains 20 IOCs — a mix of IPs and SHA-256 hashes — one per line.
The mock API returns different responses for different IOCs: clean, suspicious, malicious, and
for two IOCs it returns `429` once before succeeding, to force retry handling.

> Everything runs locally. No external API calls, no API keys required (the mock uses a dummy
> key to practice the auth pattern). No external targets.

## Scenario
Meridian Financial's SIEM raised 20 IOCs in the last hour. You need to enrich each one against
your threat-intel API (mocked here) and produce a report: which IOCs are malicious, which are
clean, which are unknown, and which timed out. The lead wants the enriched data in JSON for
automated downstream processing.

## Do
1. [ ] Read the mock API source in `mock-api/app.py` to understand what responses each endpoint
   returns (which status codes, for which IOCs). Don't run the reference yet — you'll use it as a
   check at the end.
2. [ ] Write your own `enrich.py` using `httpx.Client`:
   - Load the (dummy) API key from `os.environ.get("VT_API_KEY", "demo-key")`.
   - Set a `timeout=httpx.Timeout(connect=5.0, read=10.0)` on the client.
   - Iterate over `data/iocs.txt` line by line.
   - For each IOC, detect type (IP vs hash), call the correct endpoint.
   - Accumulate results in a list of dicts.
3. [ ] Handle each HTTP status:
   - `200`: parse and store the result.
   - `404`: mark as "unknown" and continue.
   - `429`: sleep 2 s and retry once. If it fails again, mark as "rate-limited".
   - `500`/`503`: mark as "error" and continue.
4. [ ] Write the accumulated results to `output/enriched.json` using `json.dump`.
5. [ ] Print a terminal summary: counts of malicious / clean / unknown / error.
6. [ ] Run `make demo` to compare your output against the reference `enrich.py`. Do the same IOCs
   come back malicious? Did you handle the retry (`429`) the same way? Where you differ, find out why.

## Success criteria — you're done when
- [ ] `enrich.py` processes all 20 IOCs without crashing.
- [ ] The two IOCs that trigger `429` are retried correctly and succeed on the second attempt.
- [ ] `output/enriched.json` exists with 20 entries, each having an `ioc`, `type`, and `verdict` field.
- [ ] The terminal summary prints accurate counts.

## Deliverables
`enrich.py` + `output/enriched.json` (the sample run). Commit `enrich.py`; add `output/` to
`.gitignore`.

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
