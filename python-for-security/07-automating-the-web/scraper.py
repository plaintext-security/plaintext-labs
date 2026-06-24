#!/usr/bin/env python3
"""
Reference web scraper — link extraction + regex path discovery.

Target: OWASP Juice Shop (a real, intentionally-vulnerable modern web app),
running as the `target` container on port 3000. Juice Shop is a single-page
Angular app, so most navigation is JS-driven and few real routes appear as
plain <a href> anchors — the regex path-discovery pass is what surfaces the
real endpoints (e.g. /ftp, robots.txt-referenced paths, JS-bundle routes).
"""

import json
import re
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

START_URL = "http://target:3000/"
OUTPUT = Path(__file__).parent / "output" / "linkmap.json"
MAX_DEPTH = 3
PATH_RE = re.compile(r'(?<!["\w])/[\w/.-]+')


def scrape(start: str, max_depth: int = MAX_DEPTH) -> list[dict]:
    target_host = urlparse(start).netloc
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    results = []

    with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
        while queue:
            url, depth = queue.popleft()
            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            try:
                resp = client.get(url, follow_redirects=True)
            except httpx.RequestError as e:
                results.append({"url": url, "status": "error", "error": str(e), "source": "link"})
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.string.strip() if soup.title else ""
            entry = {
                "url": url,
                "status": resp.status_code,
                "title": title,
                "source": "link",
                "depth": depth,
            }
            results.append(entry)

            # Anchor-tag links
            for tag in soup.find_all("a", href=True):
                href = urljoin(url, tag["href"])
                parsed = urlparse(href)
                if parsed.netloc == target_host and href not in visited:
                    queue.append((href, depth + 1))

            # Regex path discovery from raw HTML
            for path in PATH_RE.findall(resp.text):
                full = f"http://{target_host}{path}"
                if full not in visited and full not in [r["url"] for r in results]:
                    try:
                        r2 = client.get(full, follow_redirects=True)
                        results.append({
                            "url": full,
                            "status": r2.status_code,
                            "title": "",
                            "source": "regex",
                            "depth": depth + 1,
                        })
                        visited.add(full)
                    except httpx.RequestError:
                        pass

    return results


def main() -> None:
    OUTPUT.parent.mkdir(exist_ok=True)
    links = scrape(START_URL)

    print(f"{'URL':<45} {'STATUS':<8} {'SOURCE':<8} TITLE")
    print("-" * 90)
    for entry in links:
        print(f"{entry['url']:<45} {str(entry.get('status','?')):<8} {entry.get('source','?'):<8} {entry.get('title','')}")

    OUTPUT.write_text(json.dumps(links, indent=2))
    linked = [e for e in links if e["source"] == "link"]
    hidden = [e for e in links if e["source"] == "regex"]
    print(f"\nFound {len(linked)} linked endpoints, {len(hidden)} via regex discovery.")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
