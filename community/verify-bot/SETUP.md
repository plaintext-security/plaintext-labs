# Plaintext verify-bot — setup

The verify-bot turns "post a screenshot in Discord" into one command: a learner runs
**`/verify repo:<their portfolio repo>`** and the bot verifies their committed `receipt.json`
files and grants the Discord completion roles they've earned. This is **recognition option B**
(option A is the [portfolio badge action](../../templates/portfolio-progress/); the deferred spine
C is server-side OAuth verification + a central dashboard).

It shares the **same** verification scheme as `make grade` / `verify_receipt.py` (imported from
`../../scripts`), so a role is granted only for receipts whose digest verifies — and, if you run in
HMAC mode, only for receipts signed by the grader key.

## What it does

1. Verifies the Discord request signature (Ed25519).
2. ACKs immediately, then in the background: reads the repo's receipts via the GitHub API,
   verifies them, and grants roles.
3. A track's **`<Track> ✓`** role is earned when the learner has a valid **capstone** receipt for
   that track; the first completed track also grants the hoisted **`Plaintext Verified`** role.

## Files

| file | purpose |
| --- | --- |
| `verify_core.py` | pure verify + tally + role logic (unit-tested in `test_verify_core.py`) |
| `github_receipts.py` | fetch receipts from a public repo via the GitHub API |
| `app.py` | Flask HTTP-interactions endpoint (signature check, deferred reply, role grant) |
| `register_commands.py` | register the `/verify` slash command (guild-scoped, instant) |

## Prerequisites

- A Discord **application + bot** (https://discord.com/developers/applications).
- The bot invited to the server with **Manage Roles**, and its highest role sitting **above** the
  `… ✓` / `Plaintext Verified` roles (Discord can't grant a role above the bot's own).
- The completion roles must exist on the server. They're defined in
  [`plaintext/community/server.yaml`](https://github.com/plaintext-security/plaintext) — run
  `discord_sync.py` there once to create them (names must match `verify_core.TRACK_META` exactly).

## Configure

```bash
export DISCORD_PUBLIC_KEY=...        # application → General Information → Public Key
export DISCORD_APPLICATION_ID=...    # application (client) id
export DISCORD_BOT_TOKEN=...         # bot token
export DISCORD_GUILD_ID=...          # the server id
# optional:
export GITHUB_TOKEN=...              # raises GitHub rate limit / allows private repos it can read
export GRADER_HMAC_KEY=...           # anti-cheat: require HMAC-signed receipts (reject unsigned)
```

## Run

```bash
python3 -m pip install -r requirements.txt
python3 test_verify_core.py            # sanity-check the verify math
python3 register_commands.py           # one-time: register /verify on the guild

# local dev (expose with e.g. `cloudflared tunnel --url http://localhost:8080` or ngrok):
python3 app.py
# production:
gunicorn -w 2 -b 0.0.0.0:8080 app:app
```

Then in the Developer Portal set **Interactions Endpoint URL** to
`https://<your-host>/interactions`. Discord sends a signed PING; the bot answers PONG and the URL
saves. Host it anywhere always-on (Fly.io, Railway, a small VM).

## Trust / honesty

Identical to the receipt model: the digest proves a receipt is unedited, **not** that grading was
proctored (answer keys live in this open repo). Running with `GRADER_HMAC_KEY` is the only mode
that resists a hand-forged receipt — it's the same key a future server-side grader (option C) would
hold. Without it, roles are portfolio-trust, not proof.

## Scale path (→ option C)

The background-thread model fits an always-on host. For true serverless (Cloudflare Workers /
Lambda), move the slow work behind a queue and let the function return the deferred ACK only — then
fold this verification into the option-C OAuth service so the bot and the web dashboard share one
verifier and one central record.
