#!/usr/bin/env python3
"""Register (or update) the /verify slash command for the Plaintext verify-bot.

Guild-scoped registration is instant (global commands take ~1h to propagate), so we register
to the one guild. Run once, and again whenever the command definition changes.

    export DISCORD_APPLICATION_ID=...   # application (client) id
    export DISCORD_BOT_TOKEN=...        # bot token
    export DISCORD_GUILD_ID=...         # the server id
    python register_commands.py
"""
from __future__ import annotations

import os
import sys

import requests

API = "https://discord.com/api/v10"

COMMAND = {
    "name": "verify",
    "type": 1,  # CHAT_INPUT
    "description": "Verify your committed Plaintext receipts and earn your completion roles.",
    "options": [
        {
            "name": "repo",
            "description": "Your portfolio repo (owner/repo or a GitHub URL).",
            "type": 3,  # STRING
            "required": True,
        }
    ],
}


def main() -> int:
    app_id = os.environ.get("DISCORD_APPLICATION_ID")
    token = os.environ.get("DISCORD_BOT_TOKEN")
    guild = os.environ.get("DISCORD_GUILD_ID")
    if not all([app_id, token, guild]):
        print("error: set DISCORD_APPLICATION_ID, DISCORD_BOT_TOKEN, DISCORD_GUILD_ID",
              file=sys.stderr)
        return 2
    r = requests.post(
        f"{API}/applications/{app_id}/guilds/{guild}/commands",
        headers={"Authorization": f"Bot {token}", "User-Agent": "plaintext-verify-bot"},
        json=COMMAND, timeout=15,
    )
    if r.status_code in (200, 201):
        print(f"Registered /verify on guild {guild}.")
        return 0
    print(f"error: {r.status_code} {r.text}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
