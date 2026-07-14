#!/usr/bin/env bash
# Mock external "scanner" for Lab 05. It does NOT scan anything real - it exists to make the
# argument-passing boundary VISIBLE: it prints, one per line, each argv element it received,
# verbatim. So if you called it safely (argument array), a hostile filename like
#   evil.txt; rm -rf /
# comes back as a SINGLE line of data. If your caller built a command string instead, the shell
# would have split it before this script ever ran - and the injected command would have executed.
#
# It is deliberately written to be safe itself: it never eval's its input; it only echoes "$@".
# Exit code mirrors a real tool: 0 = clean, 1 = "finding" (any arg contains the word MATCH),
# 2 = usage error (no args).

set -u

if [ "$#" -eq 0 ]; then
  echo "usage: vigil-scan.sh <target> [target...]" >&2
  exit 2
fi

status=0
i=1
for arg in "$@"; do
  # Print each received argument verbatim, prefixed with its index. No evaluation, ever.
  printf 'ARG[%d]=%s\n' "$i" "$arg"
  case "$arg" in
    *MATCH*) status=1 ;;
  esac
  i=$((i + 1))
done

exit "$status"
