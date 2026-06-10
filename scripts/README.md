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

Verify a receipt (what a public verification page / a reviewer runs):

```bash
python3 scripts/verify_receipt.py path/to/receipt.json      # digest only
GRADER_HMAC_KEY=... python3 scripts/verify_receipt.py receipt.json   # + HMAC
```

It recomputes the digest (and HMAC if keyed) and reports VALID/INVALID — tamper-evident.

## `track_certificate.py` — the track-completion credential

A **track certificate** is the layer above the per-lab receipts: it attests to a whole track —
every module lab *plus* the capstone — by aggregating their receipts into one `certificate.json`
and re-digesting the bundle. It is built **on** `verify_receipt.py` (it imports and reuses the same
digest/HMAC scheme and receipt-validation logic), so a certificate is exactly "a bundle of receipts
the verifier already trusts, plus a roll-up digest."

```bash
# Mint — gather a track's receipts from your portfolio and emit certificate.json.
# Refuses to mint if any receipt is edited, unsigned-when-keyed, or has a failing check.
python3 scripts/track_certificate.py mint \
    --track 00-foundations --name "Ada Lovelace" \
    --receipts ~/portfolio/00-foundations --out certificate.json

# Verify — recompute the cert digest + confirm each embedded receipt (reviewer / CI).
python3 scripts/track_certificate.py verify certificate.json
GRADER_HMAC_KEY=... python3 scripts/track_certificate.py verify certificate.json   # + HMAC

# Badge — a self-contained SVG + a README snippet (green only when the cert verifies).
python3 scripts/track_certificate.py badge certificate.json --out-svg badge.svg
```

The certificate's trust model is **identical** to the receipt's (see above): VALID means
tamper-evident and internally consistent, not proctored. The **public verification page** on the
MkDocs site (`tracks/verify.md` in the `plaintext` repo) runs the same digest check in-browser via
SubtleCrypto — its JS canonicaliser is kept byte-identical to Python's
`json.dumps(sort_keys=True)` (sorted keys, `", "`/`": "` separators, `\uXXXX` escaping) so a
learner can verify a certificate without installing anything, and honestly explains the open-repo
trust model.

### Design / paper labs (ai_rubric)
Labs that can't be auto-graded (threat modeling, reporting) use the `ai_rubric` check type: always
advisory, it surfaces the rubric for self/peer review and, if `AI_GRADER_CMD` is set, runs an
external LLM judge for draft feedback. It never gates completion.

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

## Opting a lab into CI (`.ci-demo`)

Labs CI (`.github/workflows/labs-ci.yml`) is **opt-in**: a lab's demo is run/enforced only if the
lab directory contains a `.ci-demo` marker file. This is deliberate — the curriculum intentionally
ships labs whose `make demo` is *not* expected to pass in CI:

- **learner-exercise labs** — the demo fails until the learner completes it (e.g. a Dockerfile the
  learner must write, or `# YOU:` scaffolds);
- **VM / cloud labs** — they need Windows, a hypervisor, or real cloud credentials.

Add a `.ci-demo` to a lab **only once its `make up && make demo && make down` is green on a Linux
runner**. Seeded with the validated reference exemplars (`offensive/06-web-injection`,
`defensive/08-detection-as-code`, `defensive/07-log-parsing`); grow the set as more labs are confirmed.
