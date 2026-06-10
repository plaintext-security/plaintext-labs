# Module 04 — HTTP & APIs for Enrichment

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *every IOC you can't explain is a ticket you can't close; APIs give you the context.*

## Why this matters
A bare IP address tells you nothing. An IP address with its ASN, abuse-report count, country,
and known-malware association tells you whether to escalate or deprioritize. Threat-intel
enrichment — querying VirusTotal, AbuseIPDB, Shodan, or any internal API — is the step that
transforms a raw alert into something actionable. Every SOC analyst does this by hand; every
senior engineer automates it.

## Objective
Use `httpx` to query a local mock threat-intel API; enrich a list of IOCs (IPs and hashes) from
`data/iocs.txt`; handle errors, timeouts, and rate-limiting correctly; and output enriched
results.

## The core idea
The HTTP layer is simple; the error handling is not. A script that queries an API and prints the
result on success is a demo. A tool that handles `429 Too Many Requests` (rate limiting), retries
with exponential backoff on `503`, logs and skips on `404` (unknown IOC), and times out rather
than hanging forever is production-ready. These cases are not rare — they are the normal
behaviour of any real threat-intel API under load. Build for them from the start.

`httpx` is the modern replacement for `requests` for security tooling: same interface, but async
support is built in (which matters when you need to enrich 1000 IOCs in parallel), and it has
better defaults for connection pooling and timeouts. In synchronous mode (`httpx.get(...)`) it is
a drop-in replacement. Set an explicit `timeout=` on every call; the default is no timeout, which
means a hung API call hangs your whole script. `timeout=httpx.Timeout(connect=5.0, read=30.0)` is
a reasonable starting point.

Authentication to threat-intel APIs is almost always via a header: `X-API-Key: <value>` or
`Authorization: Bearer <token>`. Load the key from the environment, never from the source file.
`httpx.Client(headers={"X-API-Key": os.environ["VT_API_KEY"]})` applies the header to every
request in a session — you set it once, not on every call. The Client context manager also
handles connection reuse across requests, which matters for rate-limiting: a single persistent
session respects the same-connection queue better than a new connection per request.

Rate limiting is the adversary. Real threat-intel APIs return `429` with a `Retry-After` header
when you exceed your quota. The correct response is: read the header, sleep that many seconds,
retry once. If there is no `Retry-After`, use exponential backoff: wait 1 s, then 2 s, then 4 s,
up to a cap. Do not retry indefinitely — set a max retry count (three is usually right) and then
log and skip the IOC. An enrichment script that hangs or crashes on rate-limiting is worse than
one that skips a few IOCs and finishes.

## Learn (~2.5 hrs)

**HTTP with httpx (~1 hr)**
- [httpx documentation — Quickstart](https://www.python-httpx.org/quickstart/) — covers the synchronous API; focus on `Client`, `get`, `post`, response status codes, and timeout configuration.
- [httpx documentation — Advanced Usage](https://www.python-httpx.org/advanced/clients/) — read the "Timeout configuration" and "Authentication" sections specifically.

**Error handling and retries (~1 hr)**
- [Exponential Backoff And Jitter — AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) — the canonical explanation of why you add jitter to backoff; short read, high value.
- [tenacity — retry library for Python](https://tenacity.readthedocs.io/en/latest/) — a clean declarative way to add retries; understand the `retry`, `wait`, and `stop` parameters.

**Threat intel API context (~30 min)**
- [VirusTotal API v3 — Getting Started](https://docs.virustotal.com/reference/overview) — skim the authentication and rate-limiting sections to understand the real API shape; the lab uses a local mock, but the real shape is what you'll hit in the field.

## Key concepts
- `httpx.Client` with session-level headers and timeouts — never per-call headers for auth
- Status-code-first response handling: check the code before reading the body
- `429` + `Retry-After`: sleep and retry; exponential backoff for other 5xx errors
- Loading API keys from environment variables only — never from source files
- Enrichment as a pipeline: iterate IOCs, query, handle error, accumulate, write results

## AI acceleration
A model writes the API query loop quickly. The hidden bugs are in the error cases: test it
against a mock API that returns `429`, `503`, and `404` in sequence. Does the model's code retry
the 429? Does it give up gracefully on repeated 503? Does it skip the 404 or crash? Those three
lines of test coverage are the difference between a script and a tool.
