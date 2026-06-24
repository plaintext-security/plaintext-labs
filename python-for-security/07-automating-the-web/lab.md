# Lab 07 — Automating the Web

*Hands-on lab · [← Back to the module concept](README.md)*

> **Lab environment: real-target rewire — validation deferred.** The crawl target is now OWASP Juice Shop (a real intentionally-vulnerable app) instead of a hand-rolled Flask page. `make up && make demo && make down` has **not** yet been re-run on a clean Linux runner; validate before marking the lab done.


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/07-automating-the-web
make up        # starts the OWASP Juice Shop target + student container
make demo      # runs the reference scraper.py and shows discovered endpoints
make shell
make down
```

The `target` container runs [OWASP Juice Shop](https://github.com/bkimminich/juice-shop)
(`bkimminich/juice-shop` on port 3000) — a real, intentionally-vulnerable modern web app. It's a
single-page Angular application: the visible navigation is rendered client-side, so most real
routes never appear as plain `<a href>` anchors in the served HTML. Beyond the landing page it
exposes a real `/ftp` directory, a `robots.txt`, and routes not shown in the top nav (for example
the score board at `/#/score-board`). The student container has `httpx` and `beautifulsoup4`
installed.

> **Authorization note:** Only scrape the local `target` container. Never run web scrapers
> against external sites without explicit written authorization from the site owner.

## Scenario
You're kicking off recon against an authorized target before a pen-test engagement. Juice Shop's
visible UI is a thin Angular shell — the interesting attack surface (file directories, hidden
routes, API paths) lives in JavaScript bundles and server-side directories, not the nav bar. Your
task: scrape the local app, build a complete link map, and surface at least one route that *isn't*
linked from the landing page — the kind of thing a pentester's spider finds in the first two
minutes.

## Do
1. [ ] Open the target app in your browser at `http://localhost:3000` and explore the visible
   navigation. Notice how few real routes are reachable as plain links — most navigation is
   JS-driven. Try `http://localhost:3000/ftp` and `http://localhost:3000/robots.txt` directly:
   these are real endpoints not shown in the top nav, and the kind of thing your scraper must
   surface. (Hold off on `make demo`; use it as a check once you've built your own.)
2. [ ] Write `scraper.py` using `httpx.Client` and `beautifulsoup4`:
   - Start at `http://target:3000/` (the compose hostname).
   - Extract all `<a href>` links from each page.
   - Follow links that stay on the same host; record all visited URLs.
   - Use a `set` to avoid visiting the same URL twice.
3. [ ] Extend the scraper to also search each page's raw HTML (including inline scripts and JS
   bundle references) for path-like strings using regex:
   ```python
   re.findall(r'(?<!["\w])/[\w/.-]+', response.text)
   ```
   Add any discovered paths to your link map. On a SPA like Juice Shop this regex pass — not the
   anchor pass — is what surfaces most real routes.
4. [ ] Print a complete link map: URL, HTTP status, page title, and whether it was found via
   `<a href>` or via the regex pass.
5. [ ] Confirm your scraper discovers at least one route that is **not** linked from the landing
   page — for example `/ftp`, a `robots.txt`-referenced path, or a path surfaced only by the
   regex/JS pass. Note which pass found it.
6. [ ] **Prove it with a test you wrote (the ownership half).** Don't leave the guards as by-hand
   checks. Write `test_scraper.py` that runs your crawl against the `target` app and asserts:
   - At least one route **not** linked from the landing page (e.g. `/ftp` or a regex-pass-only
     path) **is** in the resulting link map (discovery works).
   - An off-host URL is **not** followed — feed the crawler an external URL (e.g. inject one into
     the start set or a stubbed page) and assert no off-host URL appears in the visited set
     (the scope guard holds).
   - A 404 path **does not crash** the crawl — request a missing path and assert the crawl
     completes and records it, rather than raising.

   Have a model draft the test; read every assert; run `python -m pytest test_scraper.py` and
   confirm green. A committed test for the off-host/404 guards beats a reference diff — it survives
   leaving the lab and goes in the portfolio.
7. [ ] Run `make demo` and compare your link map against the reference scraper. Did you find every
   endpoint it did, including the unlisted ones? If it found something you missed, work out why.

## Success criteria — you're done when
- [ ] `scraper.py` discovers at least one route not linked from the landing page (e.g. `/ftp` or a
  path found only via the regex/JS pass).
- [ ] It correctly distinguishes linked endpoints from unlisted ones.
- [ ] It does not follow links off the target host (try embedding an external URL in a comment
  and confirming the scraper ignores it).
- [ ] It does not crash on a 404 response.
- [ ] `test_scraper.py` asserts unlisted-endpoint discovery, the off-host guard, and 404
  resilience, and passes under `python -m pytest test_scraper.py`.

## Deliverables
`scraper.py` + `test_scraper.py`. Commit both; add `output/` to `.gitignore` (commit
`linkmap.json` only if you want the sample run in the portfolio).

## Automate & own it
**Required.** Add a `--depth` flag to `scraper.py` (default 3) that limits how many links the
scraper follows from the starting URL. Have a model draft it using a BFS queue; review the queue
logic — does it correctly track depth per URL, or per BFS level? Commit the updated `scraper.py`
with a comment explaining the depth-limiting approach.

## AI acceleration
Ask a model for a production-safe scraper with rate limiting and depth limiting. Then test the
depth limit: does it stop at exactly 3 hops? What happens if the target is unreachable — does it
hang or time out cleanly? Verify both cases before trusting the tool.

## Connects forward
Web scraping reappears in Track 01 (Offensive) — module 02 (recon) uses the same pattern for
passive reconnaissance. In Track 10 (Security Automation), module 07 (enrichment pipelines) uses
scheduled HTTP collection for threat-feed scraping.

## Marketable proof
> "I build web scrapers for security reconnaissance — link extraction, unlisted endpoint
> discovery, session-aware HTTP — scoped to authorized targets, with rate limiting and depth
> control."

## Stretch
- Handle the case where the target uses HTTP redirects: follow the redirect chain and record
  both the original URL and the final URL in the link map.
- Add a check for `robots.txt`: before scraping, fetch `http://target:3000/robots.txt` and
  log any paths that are disallowed (don't skip them in this controlled lab, but log the note).
