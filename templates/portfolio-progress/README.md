# Plaintext portfolio progress badge

Show your Plaintext progress on your own GitHub profile — automatically, with no PRs to us
and nothing to post in Discord. This is **option A** of the completion-recognition system:
a paste-once GitHub Action that reads the `receipt.json` files you already commit and renders
a live badge + per-track table into your README.

## How it works

1. You do labs. Each `make grade` writes a verifiable `receipt.json` (see the
   [Start Here](https://plaintext-security.github.io/plaintext/start-here/) page).
2. You commit those receipts to **your own** portfolio repo (one per lab, anywhere in the tree).
3. This workflow runs on every push that touches a receipt. It:
   - downloads Plaintext's open-source verifier (`verify_receipt.py` + `progress_badge.py`),
   - verifies every receipt's digest (and HMAC, if you set the grader key) and that all its
     checks passed — **tampered or failed receipts are skipped, not counted**,
   - regenerates `.plaintext/progress.svg` and a progress table in your `README.md`.

The result on your profile README looks like:

<!-- plaintext:progress:start -->
### 🛡️ Plaintext progress

![Plaintext progress](.plaintext/progress.svg)

| Track | Progress |
| --- | --- |
| Foundations | `██████████████` 12/12 ✅ |
| Defensive Security | `███░░░░░░░░░░░` 3/16 |

_Updated 2026-06-10 · 15 verified receipts · [what is this?](https://plaintext-security.github.io/plaintext/start-here/)_
<!-- plaintext:progress:end -->

## Setup (2 minutes)

1. Copy `.github/workflows/plaintext-progress.yml` from this folder into the same path in your
   portfolio repo.
2. (Optional) Add the two markers anywhere in your `README.md` to control *where* the badge
   block lands; if you skip this, the workflow appends the block at the end:
   ```
   <!-- plaintext:progress:start -->
   <!-- plaintext:progress:end -->
   ```
3. Commit a `receipt.json` (or run the workflow manually from the **Actions** tab → *Plaintext
   progress* → *Run workflow*). Your badge appears within a minute.

## Run it locally

```bash
# from your portfolio repo, with the two scripts on your path:
python3 progress_badge.py --receipts . --readme README.md --out-svg .plaintext/progress.svg
```

## Notes

- **Supply chain:** the workflow pulls the scripts from `plaintext-labs@main`. Pin
  `PLAINTEXT_REF` to a tag or commit SHA in the workflow if you want a frozen version.
- **Honesty:** the digest proves a receipt is unedited; it does not prove grading was proctored
  (answer keys live in the open repo). The optional `GRADER_HMAC_KEY` is the only tamper-evidence
  a future server-side grader can trust. This badge is portfolio evidence, not a proctored exam.
- **Privacy:** the workflow runs entirely in your repo's Actions and only reads your own files.
