#!/usr/bin/env python3
"""Reference demo for Lab 04 — Async & Structured Concurrency.

The indicators aren't invented: we parse the shipped Suricata `data/eve.json`,
validate the `alert` events into typed `AlertEvent`s (canonical M02 model), and
derive the unique `src_ip`/`dest_ip` off them — each IP enriched exactly once.

Runs a local mock threat-intel API (in-process, so no external network) that:
  - returns JSON enrichment,
  - 429s the FIRST touch of every indicator with a `Retry-After` header (so the
    backoff path is exercised for every IP, deterministically),
  - records the MAX concurrent in-flight requests it ever saw.
Then enriches the derived indicators with BOUNDED concurrency and proves:
  1. every indicator got enriched (429s were retried, not dropped),
  2. concurrency was real but never exceeded the semaphore limit (no herd).
"""
from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))
from sift.enrich import enrich_all  # noqa: E402
from sift.models import load_alerts, unique_indicators  # noqa: E402

DIVIDER = "─" * 60
EVE = Path(__file__).parent / "data" / "eve.json"
# Semaphore limit < indicator count so the bound genuinely bites (the herd is real).
LIMIT = 3

_state = {"in_flight": 0, "max_in_flight": 0, "n_429": 0, "seen": set(), "lock": threading.Lock()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence access logs
        pass

    def do_GET(self):
        ioc = parse_qs(urlparse(self.path).query).get("ioc", [""])[0]
        with _state["lock"]:
            _state["in_flight"] += 1
            _state["max_in_flight"] = max(_state["max_in_flight"], _state["in_flight"])
            first_touch = ioc not in _state["seen"]
            _state["seen"].add(ioc)
            if first_touch:
                _state["n_429"] += 1
        try:
            # Rate-limit the first touch of every IOC → forces the Retry-After path.
            if first_touch:
                self.send_response(429)
                self.send_header("Retry-After", "0")
                self.end_headers()
                self.wfile.write(b"{}")
                return
            time.sleep(0.02)  # a little latency so overlapping requests are observable
            body = json.dumps({"ioc": ioc, "malicious": ioc.startswith("141.98.")}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        finally:
            with _state["lock"]:
                _state["in_flight"] -= 1


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("Parse eve.json → typed AlertEvents → derive indicators")
    alerts = load_alerts(EVE)
    indicators = unique_indicators(alerts)
    n = len(indicators)
    print(f"  validated alert events: {len(alerts)}")
    print(f"  unique src_ip/dest_ip indicators (deduped): {n}")
    print(f"    {', '.join(indicators)}")
    if n < 2:
        print("  DEMO FAILED — need ≥2 indicators to exercise concurrency")
        return 1

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    section(f"Enrich {n} indicators against the mock TI API, concurrency capped at {LIMIT}")
    results = asyncio.run(enrich_all(base, indicators, concurrency=LIMIT))
    server.shutdown()

    enriched = sum(1 for r in results if "malicious" in r)
    print(f"  enriched: {enriched}/{n}")
    print(f"  429s issued by the API (all retried via Retry-After): {_state['n_429']}")
    print(f"  max concurrent in-flight seen by API: {_state['max_in_flight']} (limit {LIMIT})")

    section("Result")
    ok = (enriched == n and 2 <= _state["max_in_flight"] <= LIMIT and _state["n_429"] > 0)
    print("  all enriched, 429s retried, concurrency was real AND bounded ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
