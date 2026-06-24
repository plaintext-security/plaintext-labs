# `lib/` — shared dataset cache

So a learner working through the curriculum downloads each real dataset **once**, not once per lab. Many labs use the same public artifacts (EVTX-ATTACK-SAMPLES, loghub, Malware-Traffic-Analysis.net PCAPs, abuse.ch feeds, …); this caches them in one place and gives every dataset URL a single, verified home.

## Two files

- **`sources.tsv`** — the registry. One row per real dataset: `name · type · url · sha256 · notes`. A source's URL lives here and **only** here, so it's defined and verified once. Labs reference a source by **name**, never a raw URL.
- **`fetch.sh`** — the fetcher. Source it, then call one of:
  - `fetch_file <name> [dest]` — single file; cached forever under `.cache/datasets/<name>/`.
  - `fetch_repo <name>` — `git clone --depth 1` once; returns the clone path.
  - `fetch_feed <name> [dest]` — live feed; re-downloaded only when the cached copy is older than `PLT_FEED_TTL_H` (default 24h).

All three print the cache path on stdout and download **only if absent/stale**. The cache (`<labs-root>/.cache/datasets/`) is git-ignored and survives `make reset`.

## Use it in a lab

```sh
# in a fetch-data script / Makefile recipe, run from inside the labs tree:
. "$(d=$PWD; while [ ! -f "$d/lib/fetch.sh" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/lib/fetch.sh"

fetch_file loghub-openssh data/auth.log          # copy a cached file into the lab
EVTX=$(fetch_repo evtx-attack-samples)           # use a path under the cached clone
cp "$EVTX/Execution/revshell_cmd_svchost_sysmon_1.evtx" data/
fetch_feed threatfox-recent data/threatfox.csv   # refresh a live feed (needs MB_AUTH_KEY)
```

## Notes

- **abuse.ch feeds** (`threatfox-recent`, `feodo-ipblocklist`, `urlhaus-recent`) need a free Auth-Key: `export MB_AUTH_KEY=...` (get one at <https://auth.abuse.ch/>). MalwareBazaar *samples* are pulled by hash/tag in `malware/*/fetch-sample.sh` (also needs the key) and are intentionally not cached here.
- **Malware-Traffic-Analysis.net** zips are password-protected (`infected`) and contain **live malware** — the cache stores the zip; the lab unzips deliberately, in isolation, only when needed.
- **Overrides:** `PLAINTEXT_LABS_CACHE` (cache dir), `PLT_FEED_TTL_H` (feed freshness window).
- **Adding a source:** add one row to `sources.tsv` (verify the URL once), then reference it by name. Pin `sha256` once a value is confirmed on a runner.
