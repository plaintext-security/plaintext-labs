# Lab tooling

Shared scripts used across the labs and in CI.

## `grade.py` — automated lab grading

Turns a lab's "Success criteria" into executable checks. Each lab declares a `grade.yaml`
and exposes a `make grade` target:

```bash
cd offensive/06-web-injection
make up                       # start the lab
FLAG=... make grade           # grade your work
```

### Check types
| type | what it proves |
|------|----------------|
| `flag` | you reached something only completion exposes (compared by sha256) |
| `structural` | your artifact exists and matches/avoids patterns (lint-ish) |
| `artifact_functional` | your script runs and produces the expected exit/output |
| `target_state` | the live lab is in the proven state (a fix now holds, a marker is written) |
| `advisory` | informational only (e.g. an AI rubric) — never fails the grade |

A check is required unless `required: false` (advisory checks default to optional). On an
all-pass, the grader writes **`receipt.json`** — lab id, timestamp, checks passed, artifact
hashes, and a digest — which you commit to *your own* portfolio repo.

### Trust model (be honest about it)
This is an **open** repo, so answer keys (flag hashes, held-out data) are visible. The receipt is
therefore **self-verification + portfolio evidence**, not proctoring. Set `GRADER_HMAC_KEY` to add
an HMAC a future server-side grader could verify; a real, anti-cheat credential would need
server-side grading with a private key (out of scope for the open model — see plaintext TODO T7).

### Held-out data
Where a check should prove a *general* solution (a detection that's quiet on benign data, a parser
that hits a rate on unseen logs), grade against a **held-out** set distinct from the `demo` set.
Bundling those sets is the next step (plaintext TODO T6); today those appear as `advisory` notes.

## `check_consistency.py` — prose ↔ labs lockstep

Asserts every `plaintext/tracks/<NN-track>/modules/<MM-module>/` has a matching
`plaintext-labs/<track>/<MM-module>/` (and vice-versa). Run in CI (`labs-ci.yml`); catches the
kind of numbering drift the PowerShell module insertion caused.

```bash
python3 scripts/check_consistency.py --tracks ../plaintext/tracks --labs .
```
