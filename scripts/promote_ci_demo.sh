#!/usr/bin/env bash
# promote_ci_demo.sh — add a `.ci-demo` marker to every lab that passed the survey,
# then open a PR. A lab with `.ci-demo` is enforced by labs-ci.yml going forward, so
# this is how a green survey result becomes a standing regression gate.
#
# Usage:
#   scripts/promote_ci_demo.sh GREENS_FILE     # GREENS_FILE = one lab path per line
#   scripts/promote_ci_demo.sh forensics/03-file-systems-carving defensive/01-telemetry
#
# In CI it is called by .github/workflows/labs-survey.yml with the survey's pass list.
# Run it locally after `scripts/local-lab-check.sh --all` to promote your green labs:
#   scripts/local-lab-check.sh --all | awk '$2=="PASS"{print $1}' > greens.txt
#   scripts/promote_ci_demo.sh greens.txt
#
# Opening the PR needs the GitHub CLI (`gh`) authenticated, or GH_TOKEN set (CI does this).
set -euo pipefail

cd "$(cd "$(dirname "$0")/.." && pwd)"   # repo root

# Collect lab paths from a file argument and/or positional args.
labs=()
if [ "$#" -eq 1 ] && [ -f "$1" ]; then
  while IFS= read -r l; do [ -n "$l" ] && labs+=("$l"); done < "$1"
else
  labs=("$@")
fi
[ "${#labs[@]}" -gt 0 ] || { echo "usage: $0 GREENS_FILE | LAB_PATH..."; exit 2; }

added=0
for lab in "${labs[@]}"; do
  if [ ! -d "$lab" ]; then echo "skip (missing dir):  $lab"; continue; fi
  if [ ! -f "$lab/Makefile" ]; then echo "skip (no Makefile): $lab"; continue; fi
  if [ -f "$lab/.ci-skip" ]; then echo "skip (.ci-skip):     $lab"; continue; fi
  if [ -f "$lab/.ci-demo" ]; then echo "already marked:      $lab"; continue; fi
  printf 'Survey-validated: `make %s& demo && down` passed on a clean Ubuntu+Docker runner.\n' \
    "$( grep -qE '^up:' "$lab/Makefile" && echo 'up && ' )" > "$lab/.ci-demo"
  echo "marked .ci-demo:     $lab"
  added=$((added+1))
done

echo
echo "Promoted $added lab(s)."
[ "$added" -gt 0 ] || { echo "Nothing to promote."; exit 0; }

# If we're in a git context with gh available, open a PR; otherwise leave the markers
# staged for the caller to commit.
if ! command -v gh >/dev/null 2>&1; then
  echo "gh not found — markers written to the working tree; commit + PR them yourself."
  exit 0
fi

branch="ci/promote-ci-demo-${GITHUB_RUN_ID:-local-$$}"
git config user.name  "${GIT_AUTHOR_NAME:-labs-survey}"
git config user.email "${GIT_AUTHOR_EMAIL:-labs-survey@users.noreply.github.com}"
git checkout -b "$branch"
git add -A ':(glob)**/.ci-demo'
git commit -m "labs-survey: promote $added passing labs to .ci-demo

Each marker is a lab whose 'make up && make demo && make down' passed on a clean
Ubuntu+Docker runner in the Labs Survey workflow. labs-ci.yml now enforces them."
git push -u origin "$branch"
gh pr create \
  --base main --head "$branch" \
  --title "labs-survey: promote $added passing labs to .ci-demo" \
  --body "Automated by the **Labs Survey** workflow. Each added \`.ci-demo\` marks a lab whose \`make up && make demo && make down\` passed on a clean Ubuntu+Docker runner, so \`labs-ci.yml\` will enforce it nightly going forward.

Review the survey run's job summary for the full PASS/FAIL scorecard before merging. Drop a \`.ci-skip\` (with a reason) on any lab that should *not* be CI-enforced (real cloud creds / VM / learner-exercise)."
