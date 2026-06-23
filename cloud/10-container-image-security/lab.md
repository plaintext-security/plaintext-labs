# Lab 10 — "It Runs — What Else Is In It?": Scan, Triage, and Rebuild Clean

*Variant D · breach-driven, predict-then-reveal verdict. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/10-container-image-security
make up         # pull scanner images (trivy + grype); no build required
make demo       # scan the vulnerable image + grype + node:14 + trivy config on Dockerfile.bad
make shell      # drop into a scanner shell to run your own commands
make down       # stop when done
```

The environment provides `trivy` and `grype` pre-pulled in a scanner container, plus
`data/Dockerfile.bad` (an image with the seven classic hygiene failures — `FROM latest`, secrets in
`ENV`, root user, debug port, fat install) and `data/Dockerfile.fixed` (the hardened reference; **try
the rebuild yourself before reading it**). `make demo` is deterministic and runs offline after `make up`.

> Everything runs locally against images you pull. No external targets, no authorization required.

## Scenario
The target account pushed three images to production six months ago with no scanning, and a compliance
review just flagged them — the same posture that let `docker123321`'s images sit on Docker Hub for ten
months and a credential sit in a Codecov layer for months. Your deliverable is a **verdict on what's
hidden in a working image**, the **hardened rebuild** that closes it, and the **CI gate** that stops it
recurring. Each step runs the rhythm: **Predict** (commit before you scan) → **Do** → **Reveal** →
**Record** (one line in the report).

## Do

### Part 1 — Call what's hidden, then prove it

1. [ ] **Predict the inherited CVEs.** Before scanning, write your call for `python:3.8-slim`: roughly
   how many fixable HIGH/CRITICAL CVEs does a "clean slim base you didn't write" carry — none, a
   handful, dozens? Then run `trivy image --severity HIGH,CRITICAL python:3.8-slim`.
   **Reveal & Record:** the actual count, and how many are **fixable** vs. unfixed. The fixable ones are
   "rebuild now"; note that the count is dozens, not zero — these are the base's decisions, now yours.

2. [ ] **One scanner is one opinion.** Run `grype python:3.8-slim` and reconcile against trivy. Where do
   the counts disagree, and why (different DB sources)? **Record:** one line on what disagreement means
   for trusting a single tool.

3. [ ] **Triage by fixability, not severity.** From your trivy output, separate fixable-HIGH/CRITICAL
   from unfixed. **Reveal:** gating on raw severity would block your pipeline on CVEs you *cannot* fix;
   the correct gate is severity-and-fixable. **Record:** the top three fixable CVEs and the minimum base
   bump that clears the most of them.

4. [ ] **What a CVE scan never sees.** Run `trivy config /lab/data/Dockerfile.bad` and read every
   finding. This is the `docker123321`/Codecov class — config and secrets, not CVEs.
   **Predict then Reveal:** which findings would a `trivy image` CVE scan have *missed* entirely?
   (The secrets in `ENV`, the root `USER`, `FROM latest`, the debug port — none are package CVEs.)
   **Record:** map each finding to the risk it represents, and note that **"scanned clean" ≠ "clean."**

### Part 2 — Rebuild clean, and prove the rebuild

The triage is the finding; **the rebuild is the fix** — and the fix is a *rebuild*, not a patch.

5. [ ] **Author the hardened multi-stage rebuild.** Open `data/Dockerfile.bad` and write your own
   hardened version (compare to `data/Dockerfile.fixed` only after). Apply the README's rulebook:
   **pin the base by digest** (not `latest`); use a **minimal/distroless or `-slim` final stage** via a
   **multi-stage build** so build tools and the package manager never ship; **secrets out of the image**
   (runtime injection, not `ENV`); `--no-install-recommends` and a cleaned apt cache; **copy only the
   artifact**, not the whole context; a **non-root `USER`**; drop the debug port.

6. [ ] **Prove the rebuild measurably cut the surface (graded step).** Run `make harden-verify`: it runs
   `trivy config` on both Dockerfiles and **gates on MEDIUM+** — `Dockerfile.bad` **fails** (two HIGH:
   no `USER`, missing `--no-install-recommends`, plus the tag finding), the hardened file **passes**
   (only a LOW remains). The drop from "2 HIGH" to "0 HIGH" is the rebuild's measurable result.
   Re-scan the rebuilt image for CVEs too and **Record** the before/after fixable-CVE count — the
   smaller SBOM should carry fewer inherited CVEs.

7. [ ] **Generate the SBOM.** Run `trivy image --format cyclonedx --output sbom.json python:3.8-slim`.
   **Record:** what the SBOM lets you answer that the CVE report alone can't (e.g. "was Log4Shell in
   anything we shipped last November?" — retrospective queries without rebuilding old images).

## Success criteria — you're done when
- [ ] You have trivy *and* grype CVE counts for `python:3.8-slim` (and `node:14`) with a fixable-vs-unfixed
  breakdown, and you predicted the count before scanning.
- [ ] You can name three `trivy config` findings in `Dockerfile.bad` that a CVE scan would have missed, and
  state in one sentence why "scanned clean" ≠ "clean."
- [ ] Your hardened Dockerfile passes `make harden-verify` (0 HIGH, down from 2) and is a **multi-stage**
  build on a **digest-pinned minimal base** with a non-root `USER` and no secrets in any layer.
- [ ] You recorded the before/after fixable-CVE count showing the rebuild shrank the inherited surface.
- [ ] You have `sbom.json` on disk and scored your three "Call it" predictions against the reveals.

## Deliverables
- `verdict-report.md` — the per-image finding: predicted vs. actual CVE count, fixable-vs-unfixed triage,
  the `trivy config` hygiene findings a CVE scan missed, and the before/after the rebuild.
- `Dockerfile.fixed` — your hardened multi-stage, digest-pinned rebuild that passes `make harden-verify`.
- `sbom.json` — the CycloneDX SBOM.

Commit these three. Lab artifacts (`*.tar`, exported layers, pulled images) stay out of the commit.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your verdict is "a working image can ship
inherited CVEs and a non-minimal base." Encode it as a **CI scan gate that fails the bad state and
passes the rebuild**: a GitHub Actions workflow (`ci-image-scan.yml`, `on: pull_request`) that builds
the image and runs **`trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed`** *plus*
**`trivy config`** to fail a non-minimal/root base. Run it against a branch with `Dockerfile.bad`
(gate fires) and one with your `Dockerfile.fixed` (gate passes), and show it flips. Have a model draft
the YAML; **review every line** — pin the `trivy-action` to a commit SHA (the supply-chain lesson
applied to your own pipeline — see the repo's own Actions-hardening, T23), confirm `--ignore-unfixed`
so the gate is actionable, and verify it fails for the *right* reason. This is your verdict made
un-recurrable — and the gate the capstone reuses.

## AI acceleration
Point a model at `trivy image --format json` output and `docker history` and ask it to rank findings by
exploitability for "an internet-facing Python API running as non-root." It produces a useful triage
order — but verify each CVE's NVD page before trusting the rank, and remember it sees the SBOM, not the
call graph: it can't tell you the vulnerable path is reachable, and it won't flag a planted miner or a
secret-in-a-layer the CVE feed doesn't list. You own the reachability call and the rebuild.

## Connects forward
- Module 08 (CI/CD security) is where this gate lives in the pipeline; the pinned-action discipline you
  applied here is the same supply-chain lesson one layer up.
- Module 11 (Container Escape & Runtime) shows what happens when the runtime protections a scan *can't*
  enforce — root, capabilities, host mounts — are actually exploited, and how Falco catches it.
- Module 13 adds a Kyverno admission webhook that enforces this gate at the cluster: an image that fails
  the scan can't even start.

## Marketable proof
> "Given a working container image, I can render the verdict on what's hidden in it — inherited CVEs
> triaged by fixability, plus the hygiene and secrets a CVE scan misses — author a hardened multi-stage,
> digest-pinned rebuild that measurably shrinks the attack surface, and encode it as a CI scan gate that
> fails the vulnerable image and passes the rebuild. I can explain why 'it runs' and 'it's clean' are
> orthogonal."

## Stretch
- Rebuild the final stage on **distroless** (`gcr.io/distroless/python3`) and compare the SBOM and CVE
  count to the `-slim` rebuild — quantify the shell-and-package-manager removal.
- Add `hadolint` to `ci-image-scan.yml` for additional Dockerfile best-practice coverage, and a `trivy
  image --scanners secret` pass to catch a Codecov-style secret baked into a layer.
- Generate an SPDX SBOM alongside CycloneDX and diff the structure.
