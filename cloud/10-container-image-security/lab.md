# Lab 10 — "It Runs — What Else Is In It?": Scan, Triage, and Rebuild Clean

> **Hands-on lab.** Environment: `plaintext-labs/cloud/10-container-image-security` (runs **local &
> offline** after `make up` — `trivy` + `grype` in a scanner container, no cloud account). Objective:
> **render a verdict on what's hidden in a working image, harden it, and make the fix a CI gate.**
> Target: **~90 min**, one finish line.

*Variant D · breach-driven, predict-then-reveal verdict. [← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **`FROM` inherits the base's CVEs.** | You ship someone else's decisions — audit the whole chain above you, not just your code. |
| 2 | **Fixability, not count, is the verdict.** | Gate on severity-*and*-fixable; a Critical with no patch is *track*, not *block*. |
| 3 | **"Scanned clean of CVEs" ≠ "clean."** | A CVE scan is blind to miners, reverse shells, secrets-in-layers, and a root/`--privileged` container. |
| 4 | **Layers remember what the running container hides.** | `docker history`/`inspect` reveal baked-in secrets and deleted files — that's how Codecov's attacker got in. |
| 5 | **One scanner is one opinion.** | `trivy` and `grype` source their CVE DBs differently — run both, reconcile the edges. |
| 6 | **The fix is a multi-stage rebuild to a minimal, pinned base — not a patch.** | Ship the artifact, not the toolchain → smaller SBOM → fewer inherited CVEs → smaller blast radius. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [verdict, revealed](README.md#the-verdict-revealed) and the [scan/hygiene diagram](README.md#the-verdict-revealed).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Your `FROM python:3.8-slim` base "just works." Whose CVEs are you now shipping — and roughly how many
   (none, a handful, dozens)?
2. A `trivy image` scan comes back clean of HIGH/CRITICAL CVEs. Name **two** dangerous things still
   dormant in the image that that report never ruled out.

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/10-container-image-security
make up             # pull trivy + grype scanners, build the lab container (no app build)
make demo           # worked pipeline: trivy + grype on the vuln image, trivy config on both Dockerfiles
make shell          # drop into the scanner shell to run your own commands
make scan-trivy IMAGE=python:3.8-slim   # trivy CVE scan of any image
make scan-grype IMAGE=python:3.8-slim   # grype second opinion
make sbom IMAGE=python:3.8-slim         # write a CycloneDX SBOM to sbom.json
make harden-verify  # the graded gate: Dockerfile.bad fails, Dockerfile.fixed passes
make down           # stop when done
```

The container ships `trivy` and `grype` pre-pulled, plus `data/Dockerfile.bad` (the target account's
image — seven classic hygiene failures: `FROM latest`, secrets in `ENV`, `COPY .`, root user, debug
port `5678`, fat install) and `data/Dockerfile.fixed` (the hardened reference — **try the rebuild
yourself before you read it**). `make demo` is deterministic and runs offline after `make up`.

> **▸ On track if:** `make demo` prints a **trivy HIGH/CRITICAL table for `python:3.8-slim` with dozens
> of rows** (not zero — EOL base), a **grype** count for the same image, and a **`trivy config`** block
> for `Dockerfile.bad` flagging the root user, the `latest` tag, and the secrets in `ENV`. The env is live.

> **Authorization note.** Everything runs locally against images you pull. No external targets, no
> authorization required.

---

## Scenario

The target account pushed three images to production six months ago with no scanning, and a compliance
review just flagged them — the same posture that let `docker123321`'s images sit on Docker Hub for ten
months and a credential sit in a Codecov layer for months. Your deliverable is a **verdict on what's
hidden in a working image**, the **hardened rebuild** that closes it, and the **CI gate** that stops it
recurring. Each step runs the same rhythm: **Predict** (commit before you scan) → **Do** → **Reveal** →
**Record** (one line in the report).

---

## Build it — read a little, do a little

### Step 1 — The inherited CVEs (whose decisions are you shipping?)

**Concept (30 sec):** Flight-card #1. `python:3.8-slim` is a frozen Debian rootfs + Python + their
transitive packages. Its CVEs are yours the moment you write `FROM`.

**Predict, then do:** write your count (none / handful / dozens), then scan:
`make scan-trivy IMAGE=python:3.8-slim`.

> **▸ On track if:** the table returns **dozens of HIGH/CRITICAL rows** (an EOL slim base — not zero,
> not a handful), each with a `Library`, `Installed Version`, and a `Fixed Version` column. **Record:**
> the total, and that these are the base's decisions, now yours.

### Step 2 — Fixability, not count (and a second opinion)

**Concept (30 sec):** Flight-cards #2 and #5. The count is a distraction; **fixable HIGH/CRITICAL** is
the verdict. And one scanner is one opinion.

**Do it:** re-read the trivy table — every row with a non-empty **`Fixed Version`** is "rebuild now";
the blanks are "track, don't gate." Then run the second opinion: `make scan-grype IMAGE=python:3.8-slim`.

> **▸ On track if:** you can split the trivy rows into **fixable vs. unfixed**, and grype's total
> **disagrees at the edges** with trivy's (different DB sources — NVD · GHSA · distro vs. the Anchore
> feed). **Record:** the top three fixable CVEs, the minimum base bump that clears the most, and one
> line on why a single scanner is one opinion.

### Step 3 — What a CVE scan never sees (the docker123321 / Codecov class)

**Concept (30 sec):** Flight-card #3. This is the hygiene axis — config and secrets, not packages. A
clean CVE report says nothing here.

**Predict, then do:** name two findings you expect, then run `make shell` and
`trivy config /lab/data/Dockerfile.bad` (or read it in `make demo`'s step 4).

> **▸ On track if:** the config scan flags — **none of these are package CVEs** — the missing non-root
> `USER` (**runs as root**), `FROM ...:latest`, `apt-get install` without `--no-install-recommends`, and
> you can *also* eyeball two things `trivy config` alone under-weights: the **`DB_PASSWORD` /
> `AWS_SECRET_ACCESS_KEY` baked into `ENV`** and the **debug port `EXPOSE 5678`**. **Record:** map each
> finding to its risk and write the one sentence — *"scanned clean" ≠ "clean."*

### Step 4 — Rebuild clean (the fix is a rebuild, not a patch)

**Concept (30 sec):** Flight-card #6. You can't `apt upgrade` out of an inherited base — you rebuild
from a minimal, current, **pinned** base, copying only the artifact.

**Do it:** open `data/Dockerfile.bad` and author your own hardened version (compare to
`data/Dockerfile.fixed` **only after**). Apply the rulebook: **pin the base by digest** (not `latest`);
**multi-stage** so build tools / the package manager never ship; **secrets out of the image** (runtime
injection, not `ENV`); `--no-install-recommends` + cleaned apt cache; **copy only the artifact**; a
**non-root `USER`**; drop the debug port.

> **▸ On track if:** your Dockerfile pins `FROM ...@sha256:...`, declares a `USER`, has no secret in any
> `ENV`/`ARG`, and exposes only the app port. If any of those is missing, it won't pass the gate below.

### Step 5 — Prove the rebuild (graded), and generate the SBOM

**Concept (30 sec):** the triage is the finding; the **measurable drop** is the proof.

**Do it:** run `make harden-verify`, then `make sbom IMAGE=python:3.8-slim`.

> **▸ On track if:** `harden-verify` shows **`Dockerfile.bad` FAILS** (non-zero exit — two HIGH: no
> `USER`, missing `--no-install-recommends`, plus the `latest`-tag finding) and **`Dockerfile.fixed`
> PASSES** (exit 0 — only a LOW remains). That **2 HIGH → 0 HIGH** flip *is* the rebuild's result.
> `sbom.json` lands on disk in CycloneDX. **Record:** the before/after — the smaller SBOM carries fewer
> inherited CVEs — and what the SBOM answers that a CVE report can't (*"was Log4Shell in anything we
> shipped last November?"* without rebuilding old images).

---

## Prove the control (your finish line)

One motion, verified two ways:

1. **The scan surfaces the hidden, the rebuild reduces it.** `Dockerfile.bad`'s CVEs + hygiene findings
   are on the page; your hardened rebuild **passes `make harden-verify` (0 HIGH, down from 2)** and
   re-scans to a **smaller fixable-CVE count**. If the gate doesn't flip, the fix isn't proven.
2. **The verdict becomes code.** Your `Automate & own it` CI gate **fails** the bad image and **passes**
   the rebuild — the verdict made un-recurrable.

Score your two warm-up predictions (and the README's three "Call it" questions) against the reveals; note
which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. Your `FROM python:3.8-slim` "just works" — whose CVEs are you shipping, and why doesn't writing clean
   code reduce that count?
2. A `trivy image` scan is clean of fixable HIGH/CRITICAL. Name two dangerous things that report still
   does not rule out — and the tool that *would* catch them.
3. Why is the fix a multi-stage rebuild rather than `apt upgrade`, and what does the final stage *not*
   contain?

---

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

## Definition of done (`container-image-security` ✅)

- [ ] You have **trivy *and* grype** CVE counts for `python:3.8-slim` with a fixable-vs-unfixed split, and
  you predicted the count before scanning.
- [ ] You can name three `trivy config` findings in `Dockerfile.bad` that a CVE scan would have missed,
  and state in one sentence why "scanned clean" ≠ "clean."
- [ ] Your hardened Dockerfile **passes `make harden-verify` (0 HIGH, down from 2)** and is a
  **multi-stage** build on a **digest-pinned minimal base** with a non-root `USER` and no secrets in any layer.
- [ ] You recorded the before/after fixable-CVE count showing the rebuild shrank the inherited surface.
- [ ] `sbom.json` is on disk, and the CI gate flips (fails `Dockerfile.bad`, passes `Dockerfile.fixed`).
- [ ] You can explain all six flight-card facts cold.

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
