#!/usr/bin/env sh
# plaintext-labs — shared dataset cache.
#
# Each real dataset downloads ONCE into .cache/datasets/ and is reused by every
# lab and across `make reset`. Sources are declared in lib/sources.tsv so each
# URL lives — and is verified — in exactly ONE place; labs reference a source by
# NAME, never a raw URL.
#
# Usage from a lab (e.g. a fetch-data script or Makefile recipe), run from
# inside the labs tree:
#     . "$(d=$PWD; while [ ! -f "$d/lib/fetch.sh" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/lib/fetch.sh"
#     path=$(fetch_file loghub-openssh)        # single file  -> cache path
#     repo=$(fetch_repo evtx-attack-samples)   # git repo     -> cached clone path
#     feed=$(fetch_feed threatfox-recent)      # live feed    -> cache path (re-fetch if stale)
#     cp "$path" data/auth.log                 # then use it however the lab needs
#
# abuse.ch feeds need a free Auth-Key: export MB_AUTH_KEY (https://auth.abuse.ch/).
# Override the cache location with PLAINTEXT_LABS_CACHE; feed TTL with PLT_FEED_TTL_H.
set -eu

plt_root() {
  d=$PWD
  while [ "$d" != "/" ]; do
    [ -f "$d/lib/sources.tsv" ] && { printf '%s\n' "$d"; return 0; }
    d=$(dirname "$d")
  done
  echo "plaintext-labs root not found (no lib/sources.tsv above $PWD)" >&2
  return 1
}
plt_cache() { printf '%s\n' "${PLAINTEXT_LABS_CACHE:-$(plt_root)/.cache/datasets}"; }

# _src NAME FIELD   (FIELD: type|url|sha|notes)
_src() {
  awk -F'\t' -v n="$1" -v f="$2" '
    $1 ~ /^#/ { next }
    $1 == n {
      if (f=="type") print $2; else if (f=="url") print $3;
      else if (f=="sha") print $4; else if (f=="notes") print $5; ok=1
    }
    END { if (!ok) exit 3 }' "$(plt_root)/lib/sources.tsv"
}

_dl() {  # _dl URL OUTFILE NOTES
  _u=$1; _o=$2; _n=${3:-}
  case "$_n" in
    *auth=abusech*)
      [ -n "${MB_AUTH_KEY:-}" ] || { echo "  MB_AUTH_KEY unset — free key at https://auth.abuse.ch/ , then: export MB_AUTH_KEY=..." >&2; return 2; }
      curl -fsSL -H "Auth-Key: ${MB_AUTH_KEY}" "$_u" -o "$_o" ;;
    *) curl -fsSL "$_u" -o "$_o" ;;
  esac
}

_cache_path() {  # _cache_path NAME URL  -> file path in cache
  _b=$(basename "$2" | sed 's/[?].*$//')
  case "$_b" in ""|recent|csv|api) _b=feed ;; esac
  printf '%s/%s/%s\n' "$(plt_cache)" "$1" "$_b"
}

# fetch_file NAME [DEST] — ensure a single-file source is cached; print its path (or copy to DEST)
fetch_file() {
  _n=$1; _dest=${2:-}
  _url=$(_src "$_n" url) || { echo "unknown source: $_n (add it to lib/sources.tsv)" >&2; return 3; }
  _notes=$(_src "$_n" notes 2>/dev/null || true)
  _f=$(_cache_path "$_n" "$_url")
  if [ ! -s "$_f" ]; then mkdir -p "$(dirname "$_f")"; echo "[fetch] $_n" >&2; _dl "$_url" "$_f" "$_notes" || return 1
  else echo "[cache] $_n" >&2; fi
  if [ -n "$_dest" ]; then cp "$_f" "$_dest"; printf '%s\n' "$_dest"; else printf '%s\n' "$_f"; fi
}

# fetch_feed NAME [DEST] — like fetch_file, but re-fetch if the cached copy is older than PLT_FEED_TTL_H (default 24h)
fetch_feed() {
  _n=$1; _dest=${2:-}
  _url=$(_src "$_n" url) || { echo "unknown source: $_n" >&2; return 3; }
  _notes=$(_src "$_n" notes 2>/dev/null || true)
  _f=$(_cache_path "$_n" "$_url"); _ttl=${PLT_FEED_TTL_H:-24}; _stale=1
  if [ -s "$_f" ]; then
    _mt=$(stat -f %m "$_f" 2>/dev/null || stat -c %Y "$_f" 2>/dev/null || echo 0)
    [ $(( ( $(date +%s) - _mt ) / 3600 )) -lt "$_ttl" ] && _stale=0
  fi
  if [ "$_stale" -eq 1 ]; then mkdir -p "$(dirname "$_f")"; echo "[fetch] $_n (feed)" >&2; _dl "$_url" "$_f" "$_notes" || return 1
  else echo "[cache] $_n (fresh)" >&2; fi
  if [ -n "$_dest" ]; then cp "$_f" "$_dest"; printf '%s\n' "$_dest"; else printf '%s\n' "$_f"; fi
}

# fetch_repo NAME — ensure a git source is shallow-cloned in cache; print the clone path
fetch_repo() {
  _n=$1
  _url=$(_src "$_n" url) || { echo "unknown source: $_n" >&2; return 3; }
  _dir="$(plt_cache)/$_n/repo"
  if [ ! -d "$_dir/.git" ]; then mkdir -p "$(dirname "$_dir")"; echo "[fetch] clone $_n" >&2; git clone --depth 1 "$_url" "$_dir" || return 1
  else echo "[cache] $_n repo" >&2; fi
  printf '%s\n' "$_dir"
}
