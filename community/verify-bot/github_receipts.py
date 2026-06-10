#!/usr/bin/env python3
"""Fetch a learner's committed receipt.json files from a public GitHub repo.

Uses the GitHub REST API (git Trees + raw contents) — no `git clone`, so it stays light and
serverless-friendly. Returns parsed receipt dicts for `verify_core.evaluate`. An optional token
raises the rate limit and allows private repos the token can read.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests

API = "https://api.github.com"
_REPO_RE = re.compile(
    r"(?:github\.com[:/])?(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


@dataclass
class Repo:
    owner: str
    repo: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_repo(arg: str) -> Repo | None:
    """Accept 'owner/repo', a full URL, or 'github.com/owner/repo'."""
    arg = arg.strip()
    m = _REPO_RE.search(arg)
    if not m:
        return None
    return Repo(m.group("owner"), m.group("repo"))


def _headers(token: str | None) -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "plaintext-verify-bot"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def default_branch(repo: Repo, token: str | None = None, timeout: int = 10) -> str:
    r = requests.get(f"{API}/repos/{repo.slug}", headers=_headers(token), timeout=timeout)
    r.raise_for_status()
    return r.json().get("default_branch", "main")


def fetch_receipts(repo: Repo, ref: str | None = None, token: str | None = None,
                   timeout: int = 15, max_files: int = 500) -> list[dict]:
    """Return parsed receipt dicts for every receipt.json in the repo tree.

    Raises requests.HTTPError on API failure (repo missing / private without token / rate limit).
    Malformed individual receipts are skipped silently — verify_core reports them as invalid.
    """
    ref = ref or default_branch(repo, token, timeout)
    tree = requests.get(
        f"{API}/repos/{repo.slug}/git/trees/{ref}",
        headers=_headers(token), params={"recursive": "1"}, timeout=timeout,
    )
    tree.raise_for_status()
    paths = [
        item["path"] for item in tree.json().get("tree", [])
        if item.get("type") == "blob" and item["path"].endswith("receipt.json")
    ][:max_files]

    receipts: list[dict] = []
    raw_base = f"https://raw.githubusercontent.com/{repo.slug}/{ref}"
    for path in paths:
        try:
            rr = requests.get(f"{raw_base}/{path}", headers={"User-Agent": "plaintext-verify-bot"},
                              timeout=timeout)
            rr.raise_for_status()
            receipts.append(json.loads(rr.text))
        except (requests.RequestException, json.JSONDecodeError):
            continue  # invalid/unreachable file — not counted, not fatal
    return receipts
