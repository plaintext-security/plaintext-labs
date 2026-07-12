#!/usr/bin/env python3
"""Reference demo for Lab 04 — Async & Structured Concurrency.

Runs a local mock threat-intel API (in-process) that:
  - returns JSON enrichment,
  - 429s ~1 in 8 requests with Retry-After (to exercise backoff),
  - records the MAX concurrent in-flight requests it ever saw.
Then enriches many indicators with BOUNDED concurrency and proves:
  1. every indicator got enriched (429s were retried, not dropped),
  2. concurrency never exceeded the semaphore limit (no thundering herd).
"""
from __future__ import annotations

import asyncio
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))
from sift.enrich import enrich_all  # noqa: E402

DIVIDER = "─" * 60
LIMIT = 8
N = 120

_state = {"in_flight": 0, "max_in_flight": 0, "n_429": 0, "seen": 0, "lock": threading.Lock()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence access logs
        pass

    def do_GET(self):
        with _state["lock"]:
            _state["seen"] += 1
            n = _state["seen"]
            _state["in_flight"] += 1
            _state["max_in_flight"] = max(_state["max_in_flight"], _state["in_flight"])
        try:
            # 429 every 8th *first-touch* request, with a short Retry-After.
            if n % 8 == 0:
                with _state["lock"]:
                    _state["n_429"] += 1
                self.send_response(429)
                self.send_header("Retry-After", "0")
                self.end_headers()
                self.wfile.write(b"{}")
                return
            import time
            time.sleep(0.01)  # simulate a little latency so concurrency is observable
            body = json.dumps({"malicious": n % 3 == 0}).encode()
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
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    section(f"Enrich {N} indicators, concurrency capped at {LIMIT}")
    indicators = [f"10.0.0.{i}" for i in range(N)]
    results = asyncio.run(enrich_all(base, indicators, concurrency=LIMIT))
    server.shutdown()

    enriched = sum(1 for r in results if "malicious" in r)
    print(f"  enriched: {enriched}/{N}")
    print(f"  429s issued by the API (all retried): {_state['n_429']}")
    print(f"  max concurrent in-flight seen by API: {_state['max_in_flight']} (limit {LIMIT})")

    section("Result")
    ok = (enriched == N and 2 <= _state["max_in_flight"] <= LIMIT and _state["n_429"] > 0)
    print("  all enriched, 429s retried, concurrency was real AND bounded ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
