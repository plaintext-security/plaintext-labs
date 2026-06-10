# Lab 07 — Automating the Web

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/07-automating-the-web
make up        # starts the Flask target app + student container
make demo      # runs the reference scraper.py and shows discovered endpoints
make shell
make down
```

The lab runs a simple Flask web app (`target` container) with several pages: an index, a public
product listing, an "about" page, and a hidden `/internal/status` endpoint not linked from the
nav but referenced in a JavaScript comment. The student container has `httpx` and
`beautifulsoup4` installed.

> **Authorization note:** Only scrape the local `target` container. Never run web scrapers
> against external sites without explicit written authorization from the site owner.

## Scenario
Meridian's security team wants to audit the company's internal tool catalog for forgotten or
unlisted endpoints before the external pen-test engagement starts. Your task: scrape the local
web app, build a complete link map, and identify any endpoints that aren't reachable from the
main navigation — the kind of thing a pentester's spider would find in the first two minutes.

## Do
1. [ ] Open the target app in your browser at `http://localhost:5000` and explore the navigation.
   Confirm that `/internal/status` is not linked anywhere visible — this is the endpoint your
   scraper must surface. (Hold off on `make demo`; use it as a check once you've built your own.)
2. [ ] Write `scraper.py` using `httpx.Client` and `beautifulsoup4`:
   - Start at `http://target:5000/` (the compose hostname).
   - Extract all `<a href>` links from each page.
   - Follow links that stay on the same host; record all visited URLs.
   - Use a `set` to avoid visiting the same URL twice.
3. [ ] Extend the scraper to also search each page's raw HTML for path-like strings using regex:
   ```python
   re.findall(r'(?<!["\w])/[\w/.-]+', response.text)
   ```
   Add any discovered paths to your link map.
4. [ ] Print a complete link map: URL, HTTP status, page title, and whether it was found via
   `<a href>` or via the regex pass.
5. [ ] Confirm that `/internal/status` is discovered by the regex pass (it's embedded in a
   JavaScript comment, not an anchor tag).
6. [ ] Run `make demo` and compare your link map against the reference scraper. Did you find every
   endpoint it did, including the hidden one? If it found something you missed, work out why.

## Success criteria — you're done when
- [ ] `scraper.py` discovers all pages including `/internal/status`.
- [ ] It correctly distinguishes linked endpoints from unlisted ones.
- [ ] It does not follow links off the target host (try embedding an external URL in a comment
  and confirming the scraper ignores it).
- [ ] It does not crash on a 404 response.

## Deliverables
`scraper.py` + `output/linkmap.json` (the discovered endpoints). Commit `scraper.py`; add
`output/` to `.gitignore`.

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
- Add a check for `robots.txt`: before scraping, fetch `http://target:5000/robots.txt` and
  log any paths that are disallowed (don't skip them in this controlled lab, but log the note).
