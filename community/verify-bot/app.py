#!/usr/bin/env python3
"""Plaintext Discord verify-bot — HTTP Interactions endpoint (recognition option B).

A learner runs `/verify repo:<their portfolio repo>` in Discord. This:
  1. verifies the request's Ed25519 signature (Discord requirement),
  2. ACKs immediately with a deferred response (Discord's 3-second rule), then in a
     background thread fetches the repo's receipts, verifies them with `verify_core`,
     grants the earned completion roles, and edits the reply with a summary.

It replaces "screenshot your work and post it in Discord" with one slash command, and grants
roles only for receipts whose digest verifies — so the role actually means something.

Run as a small always-on web service (Fly.io / Railway / a VM). See SETUP.md. Env:
  DISCORD_PUBLIC_KEY      application public key (for signature verification)
  DISCORD_APPLICATION_ID  application (client) id  — for follow-up webhook
  DISCORD_BOT_TOKEN       bot token               — for role grants
  DISCORD_GUILD_ID        the server id
  GITHUB_TOKEN            (optional) raises GitHub rate limit / allows private repos
  GRADER_HMAC_KEY         (optional) require HMAC-signed receipts (real anti-cheat)
"""
from __future__ import annotations

import os
import threading

import requests
from flask import Flask, abort, jsonify, request
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

import verify_core as vc
from github_receipts import fetch_receipts, parse_repo

API = "https://discord.com/api/v10"

PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")
APP_ID = os.environ.get("DISCORD_APPLICATION_ID", "")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or None

# Interaction + response type constants (Discord API).
PING, APP_COMMAND = 1, 2
PONG = 1
DEFERRED = 5            # ACK now, edit the message later
EPHEMERAL = 1 << 6      # flag: only the invoker sees the reply

app = Flask(__name__)


def _bot_headers() -> dict[str, str]:
    return {"Authorization": f"Bot {BOT_TOKEN}", "User-Agent": "plaintext-verify-bot"}


def _verify_signature() -> None:
    """Abort 401 unless the request carries a valid Ed25519 signature from Discord."""
    sig = request.headers.get("X-Signature-Ed25519", "")
    ts = request.headers.get("X-Signature-Timestamp", "")
    if not sig or not ts:
        abort(401, "missing signature")
    try:
        VerifyKey(bytes.fromhex(PUBLIC_KEY)).verify(
            (ts + request.data.decode()).encode(), bytes.fromhex(sig)
        )
    except (BadSignatureError, ValueError):
        abort(401, "bad signature")


def _guild_role_ids() -> dict[str, str]:
    """Map role name -> role id for the guild (so we can grant by name)."""
    r = requests.get(f"{API}/guilds/{GUILD_ID}/roles", headers=_bot_headers(), timeout=10)
    r.raise_for_status()
    return {role["name"]: role["id"] for role in r.json()}


def _grant_roles(user_id: str, role_names: list[str]) -> tuple[list[str], list[str]]:
    """Grant each named role to the member. Returns (granted, missing_role_names)."""
    ids = _guild_role_ids()
    granted, missing = [], []
    for name in role_names:
        rid = ids.get(name)
        if not rid:
            missing.append(name)
            continue
        resp = requests.put(
            f"{API}/guilds/{GUILD_ID}/members/{user_id}/roles/{rid}",
            headers=_bot_headers(), timeout=10,
        )
        if resp.status_code in (201, 204):
            granted.append(name)
        else:
            missing.append(name)
    return granted, missing


def _followup(token: str, content: str) -> None:
    """Edit the original deferred response with the final summary."""
    requests.patch(
        f"{API}/webhooks/{APP_ID}/{token}/messages/@original",
        json={"content": content}, timeout=10,
    )


def _do_verify(token: str, user_id: str, repo_arg: str) -> None:
    """Background worker: fetch → verify → grant roles → edit the reply."""
    repo = parse_repo(repo_arg)
    if repo is None:
        _followup(token, f"❌ `{repo_arg}` isn't a GitHub repo. Try `owner/repo` or a repo URL.")
        return
    try:
        receipts = fetch_receipts(repo, token=GITHUB_TOKEN)
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        hint = " (private repo? the bot can only read public repos unless GITHUB_TOKEN can see it)" \
            if code in (403, 404) else ""
        _followup(token, f"❌ Couldn't read `{repo.slug}` (HTTP {code}){hint}.")
        return
    except requests.RequestException:
        _followup(token, "❌ GitHub request failed — try again in a moment.")
        return

    out = vc.evaluate(receipts)
    lines = [f"🔎 Verified **{repo.slug}** — {out.valid_count} valid receipt(s).", ""]
    lines += vc.summary_lines(out)

    if out.earned_roles:
        try:
            granted, missing = _grant_roles(user_id, out.earned_roles)
            if missing:
                lines.append("")
                lines.append("⚠️ These roles aren't on the server yet (ask a Maintainer to sync "
                             "server.yaml): " + ", ".join(f"`{m}`" for m in missing))
        except requests.RequestException:
            lines.append("")
            lines.append("⚠️ Verified your work but couldn't assign roles (bot permissions?).")
    _followup(token, "\n".join(lines))


@app.post("/interactions")
def interactions():
    _verify_signature()
    body = request.get_json(silent=True) or {}
    itype = body.get("type")

    if itype == PING:
        return jsonify({"type": PONG})

    if itype == APP_COMMAND and body.get("data", {}).get("name") == "verify":
        opts = {o["name"]: o.get("value") for o in body["data"].get("options", [])}
        repo_arg = (opts.get("repo") or "").strip()
        member = body.get("member") or {}
        user_id = (member.get("user") or {}).get("id") or (body.get("user") or {}).get("id", "")
        token = body["token"]
        # ACK within 3s; do the slow work (GitHub + role grant) in the background.
        threading.Thread(target=_do_verify, args=(token, user_id, repo_arg), daemon=True).start()
        return jsonify({"type": DEFERRED, "data": {"flags": EPHEMERAL}})

    abort(400, "unhandled interaction")


@app.get("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
