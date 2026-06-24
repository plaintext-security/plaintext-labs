# Module 07 — Automating the Web

*Type 9 · Tool-Build — build an `httpx` + `beautifulsoup4` scraper that extracts links, finds hidden endpoints, and follows redirect chains against a bounded local target, proven by a `test_scraper.py` that pins endpoint discovery, the off-host scope guard, and 404 resilience. Only scrape hosts you own or are permitted to test. (Secondary: Build-&-Operate — scope and session handling that keeps the crawl safe at scale.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Python for Security** — *an unprotected endpoint is only hidden if nobody looks; a scraper looks.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
Web scraping is a reconnaissance skill, a data-collection skill, and an automation skill in one.
Security engineers scrape for exposed configuration files, forgotten admin endpoints, and leaked
credentials. Automation engineers scrape to collect threat data from sites that don't offer an
API. The same techniques apply to both, and the line between "responsible automation" and
"unauthorized access" is authorization and scope — not the tool.

## Objective
Use `httpx` and `beautifulsoup4` to scrape a local web application: extract all links, identify
hidden or unlisted endpoints, and follow a redirect chain — and **prove it with a test you wrote**:
a `test_scraper.py` that asserts the hidden endpoint is discovered, the off-host guard holds, and a
404 doesn't crash the crawl. Building the scraper and committing a test that pins those behaviours
are equal halves — all within a clearly bounded local target, never against external hosts without
permission.

## The core idea
HTTP is a text protocol. A web scraper is a program that sends HTTP requests and parses the text
responses — mechanically identical to what a browser does, minus the JavaScript execution and the
display rendering. `httpx` handles the HTTP; `beautifulsoup4` handles the HTML parsing. The
combination covers about 80% of practical web-scraping needs.

The key insight for security work is that web applications leak information through their
structure: links to `/admin`, comments referencing `/api/v2/internal`, `action=` attributes
pointing to unlinked endpoints, JavaScript files that embed API paths. These are not
vulnerabilities in themselves, but they are the map. `soup.find_all("a", href=True)` gets you
every explicit link; `soup.find_all(True)` gets you every tag; a regex on the raw HTML source
(`re.findall(r'/[\w/.-]+', response.text)`) surfaces paths embedded in scripts and attributes
that BeautifulSoup doesn't expose.

Session handling is the next layer: cookies, authentication tokens, and CSRF tokens are what keep
a web application's state. `httpx.Client` (the session object) automatically stores and resends
cookies across requests — you log in once and every subsequent request carries the session. This
is also what makes authenticated scraping work: log in with a `POST` to the login endpoint,
capture the session cookie, then scrape pages that require authentication.

Responsible automation means: identify yourself in the User-Agent header, respect `robots.txt`,
limit your request rate, and only scrape targets you own or have explicit permission to test. In
a professional context, web scraping of a system you don't own requires the same written
authorization as a port scan. For this lab, the target is a local Flask application you run
yourself — no external targets, ever.

## Learn (~2 hrs)

**httpx sessions (~30 min)**
- [httpx — Client documentation](https://www.python-httpx.org/advanced/clients/) — focus on the "Client Instances" and "Cookies" sections; understand how a session maintains state across requests.

**BeautifulSoup4 (~1 hr)**
- [BeautifulSoup4 — Official documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) — read the "Quick Start", "Kinds of objects", and "Searching the tree" sections; `find_all()` is 90% of what you'll use.
- [Web Scraping with BeautifulSoup — Real Python](https://realpython.com/beautiful-soup-web-scraper-python/) — worked example with good coverage of common patterns; skip the "Interact with HTML Forms" section (that's for browser automation).

**Responsible scraping (~30 min)**
- [robots.txt specification — robotstxt.org](https://www.robotstxt.org/robotstxt.html) — understand what it says and what it does not say legally; short page, worth reading in full.

## Key concepts
- `httpx.Client` as a session: cookies and headers persist across requests
- BeautifulSoup4 parse tree: `find_all()`, `get()`, `.text`, `.attrs`
- Extracting links from HTML vs. extracting paths from raw text (regex on `response.text`)
- Following redirect chains with `httpx` (by default it follows; `follow_redirects=False` to inspect)
- Responsible automation: User-Agent, `robots.txt`, rate-limiting, scope limitation
- Verify by test, not by eye: a learner-written `test_scraper.py` that asserts hidden-endpoint discovery, the off-host guard, and 404 resilience — the ownership half, not a diff against `make demo`

## AI acceleration
A model will write the scraper quickly. The missing piece is usually the scope: the model will
write code that follows links off the target domain if you don't specify `urlparse(url).netloc ==
target_host` as a filter. Test it against a URL that resolves to an external site — does it
follow the link? Does it have a depth limit? These are the production safety checks.
