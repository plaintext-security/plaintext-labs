"""Async enricher — concurrent, but BOUNDED, and polite about rate limits.

The copilot writes a sync loop (slow) or an unbounded `asyncio.gather` over 10k
tasks (a thundering herd that gets you rate-limited or banned). The right shape:
a semaphore bounds in-flight requests, and 429s are retried with backoff that
honors `Retry-After`.
"""
from __future__ import annotations

import asyncio

import httpx


async def enrich_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    base: str,
    indicator: str,
    max_retries: int = 5,
) -> dict:
    """Enrich a single indicator; retry on 429 honoring Retry-After."""
    async with sem:  # bound concurrency — never more than N in flight
        for attempt in range(max_retries):
            r = await client.get(f"{base}/enrich", params={"ioc": indicator})
            if r.status_code == 429:
                retry_after = float(r.headers.get("Retry-After", "0") or 0)
                backoff = retry_after or 0.1 * (2**attempt)  # honor server, else exponential
                await asyncio.sleep(backoff)
                continue
            r.raise_for_status()
            return r.json()
    raise RuntimeError(f"gave up enriching {indicator} after {max_retries} tries")


async def enrich_all(base: str, indicators: list[str], concurrency: int = 10) -> list[dict]:
    """Enrich many indicators concurrently, capped at `concurrency` in flight."""
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
        return await asyncio.gather(
            *(enrich_one(client, sem, base, i) for i in indicators)
        )
