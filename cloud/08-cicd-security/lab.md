# Lab 08 — Predict the Injection Point, Then Harden the Pipeline

*Variant D · breach-driven, build-first. [← Back to the module concept](README.md)*

> **Hands-on lab.** Environment: `plaintext-labs/cloud/08-cicd-security` (one container pinning
> **gitleaks** 8.x + **trivy** 0.52.x — no cloud account for the find-half). Objective: **predict where a
> SolarWinds-style attacker injects, then author a hardened, provenance-gated pipeline that fails the
> breach-shaped build and passes a clean one.** Target: **~90–120 min**, one finish line.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The build — between trusted source and trusted signature — is the highest-trust, least-watched stage.** | SUNBURST went in *there*, not the repo. That distance is the attack surface. |
| 2 | **Signing proves WHO built it, not WHAT they built.** | A valid signature verified perfectly on a backdoored binary. Provenance is the missing link. |
| 3 | **Provenance/attestation is the *gate*.** | Demand a signed attestation tying artifact → source commit + trusted builder *before* deploy — it fails the SolarWinds build even though the signature passes. |
| 4 | **Pin every action/dependency to an immutable SHA, not a tag.** | A re-pointed tag silently changes what runs — this repo's **T23** pattern. |
| 5 | **Least-privilege pipeline auth: OIDC, minimal `permissions:`, sanitised `${{ }}`.** | A compromised build can't exfiltrate a standing credential or inject through an expression. |
| 6 | **The find-half (gitleaks, trivy, SBOM) scans *inputs*, not the process.** | Necessary but not sufficient — none of the three would have caught SUNBURST. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [injection point, revealed](README.md#the-injection-point-revealed).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. In `commit → source → build → sign → publish`, **where** did SUNBURST inject — and why does the
   popular guess ("bad code in the repo") miss?
2. Orion's signature verified perfectly. Name **what it proved** and **what it crucially did not.**

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/08-cicd-security
make up          # build the lab container + seed the git repo with planted secrets
make demo        # run both scanners + list the workflow's planted issues
make shell       # drop into the container to work
make gitleaks    # gitleaks against data/repo (prints the finding RuleIDs)
make trivy-scan  # trivy against the first image in data/images.txt (needs network)
make down        # stop when done
```

`data/repo/` is a small git repo with planted secrets (a fake AWS key in `deploy.sh`, a fake private
key in `terraform.tfvars`); `data/workflow.yml` is a GitHub Actions workflow with **7 deliberate
misconfigurations** (each tagged `# ISSUE`); `data/images.txt` lists image references for trivy. The
gitleaks and workflow work are fully offline; the trivy image scan pulls public image metadata, so it
needs network.

> **▸ On track if:** `make demo` prints (1) gitleaks **RuleIDs** for the seeded findings (an AWS access
> key and a `private-key`), (2) a tail of trivy HIGH/CRITICAL CVEs for `python:3.8-slim`, and (3) the
> **7** `# ISSUE` lines grepped from `data/workflow.yml`. If all three print, the environment is live.

**What this lab is — and isn't (read this).** You run the *find-half* for real (gitleaks and trivy
genuinely scan). The *build-half* — provenance/attestation, OIDC — you **author and reason about**: a
SLSA provenance attestation is produced by a real CI platform (GitHub-hosted Actions, a hardened
builder), which this local container is not. So you'll *write* the attesting workflow and verify its
**logic** (does it gate on provenance? does it mint OIDC instead of a standing secret?), marked
*assessed from config*, not *executed in prod*. Honest tool, honest answer.

> **Authorization note.** Only scan repositories and images you own or have explicit written permission
> to scan. Everything here runs locally against seed data you own.

---

## Scenario

The target account is wiring its deployment pipeline to the production AWS account and asked for a
review after reading the SolarWinds post-mortem. The existing `data/workflow.yml` builds an image and
ships it. Your deliverable is the **hardened, provenance-gated workflow** — plus the audit that
justifies it. You predict the injection point *first*, then harden where the prediction lands.

Each step runs the rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Step 1 — Walk the path, predict the injection point

**Concept (30 sec):** Flight-card #1. Everything we're trained to guard — code review, branch
protection, signed commits — guards the *source* arrow. The dangerous distance is the one *after* it.

**Predict, then do:** read `data/workflow.yml` end to end and draw the trust path
(commit → checkout → build image → push → deploy). Mark where a SolarWinds-style attacker injects, and
which existing step (if any) would catch them. **Record your call before touching a tool.**

> **▸ On track if:** you have a written, *pre-reveal* prediction on paper (owner of the vulnerable
> stage + the control you think guards it). Being wrong here is the teaching event — you'll score it in
> Step 4.

### Step 2 — Run the find-half: secrets (gitleaks)

**Concept (30 sec):** Flight-card #6. gitleaks guards the *source* arrow. Necessary — but it never sees
the build.

**Do it:** `make gitleaks` (or, in `make shell`,
`gitleaks detect --source /lab/data/repo --report-format json --report-path /tmp/gl.json --no-banner`).
For each finding record RuleID, file, line, commit SHA. Then add a custom rule for the target account's
token format (`_tok_[a-z0-9]{32}`) in a `.gitleaks.toml` and re-scan.

> **▸ On track if:** gitleaks prints **at least two RuleIDs** — an AWS access key (from `deploy.sh`)
> and a `private-key` (from `terraform.tfvars`) — each with a file/line/commit; your custom rule adds a
> third finding on the `_tok_…` pattern. **Reveal:** gitleaks guards the source; it would **not** have
> caught SUNBURST, which never touched the repo. **Record** that gap.

### Step 3 — Run the find-half: image + SBOM (trivy)

**Concept (30 sec):** Flight-card #6. The SBOM tells you *what's in* the artifact — never *how it was built*.

**Do it:** `make trivy-scan` scans the first image (`python:3.8-slim`). Note CRITICAL/HIGH counts and
the oldest CVE. Generate an SBOM
(`trivy image --format cyclonedx --output /tmp/sbom.json python:3.8-slim`) — record base OS and package
count. Compare the EOL tag against a current one (`python:3.12-slim`).

> **▸ On track if:** trivy reports a **nonzero** HIGH/CRITICAL count on `python:3.8-slim` and **far
> fewer** on `python:3.12-slim` — the age of the base image *is* the finding; the SBOM lists a base OS +
> a package count. **Reveal:** the SBOM attests *contents*, not *process* — the SolarWinds gap. **Record** it.

### Step 4 — Reveal the injection point

**Concept (30 sec):** Flight-card #1–2. Score your Step-1 prediction now.

**Do it:** confirm against the README — the attacker injects at the **build** step, *after* checkout and
*before* signing: past everything gitleaks and review guard, before the signature legitimises it.

> **▸ On track if:** you can state that the find-half scans **inputs, not the build process**, that the
> owner of the vulnerable stage is the pipeline's **build stage**, and that the missing control is
> **provenance.** **Record** whether your Step-1 call was right or wrong, and why.

### Step 5 — Audit the workflow's misconfigurations

**Concept (30 sec):** Flight-card #4–5. Every `# ISSUE` is a real, named CI-hardening failure.

**Do it:** `grep '# ISSUE' data/workflow.yml`, then read it. Identify each of the **7**: expression
injection via `${{ github.event.head_commit.message }}`, `permissions: write-all`, unpinned
`actions/checkout@v4`, `pull_request_target` + checkout (pwn-requests), workflow-scoped secrets, no
image scan, no secrets gate. For each: the risk, an ATT&CK technique where it fits, and the fix.

> **▸ On track if:** you named all **7** issues, each with an ATT&CK technique (e.g. T1195.002 supply
> chain, T1552 unsecured credentials) and a one-line fix.

### Step 6 — Write `workflow-hardened.yml` (the deliverable)

**Concept (30 sec):** Flight-card #4–5. This is judgment-as-code. It must:

- **Pin every `uses:` to a full commit SHA** with a trailing `# vX.Y.Z` comment (the T23 pattern).
- Declare **minimal per-job `permissions:`** (`id-token: write`, `contents: read`) — never `write-all`.
- **Mint OIDC** to assume the deploy role (`aws-actions/configure-aws-credentials` with `role-to-assume`
  + `id-token: write`) instead of long-lived `AWS_ACCESS_KEY_ID`/`SECRET` secrets.
- **Sanitise** every `${{ }}` flowing into a `run:` step (pass via `env:`, quote — never interpolate
  untrusted input into a shell).
- **Gate on the find-half:** gitleaks blocks on a secret; `trivy --exit-code 1 --severity CRITICAL,HIGH`
  blocks before push.

> **▸ On track if:** the file has **no** unpinned `uses:`, **no** `write-all`, **no** standing AWS
> secret, and gitleaks + trivy gates that can exit nonzero.

### Step 7 — Add the provenance gate (the SolarWinds control)

**Concept (30 sec):** Flight-card #2–3. This is the gate a valid signature alone sails past.

**Do it:** extend `workflow-hardened.yml` to **emit a build provenance attestation** for the image
(`actions/attest-build-provenance`, or document the `cosign attest` + SLSA-generator equivalent), and add
a deploy-side step that **verifies provenance ties the artifact to this source commit + the trusted
builder** before deploy. In a comment, state why a valid *signature* alone would still pass the
SolarWinds build but the *attestation* fails it. *(Mark this step **assessed from config** — the
attestation is produced by the real CI platform, not this container.)*

> **▸ On track if:** the workflow both **emits** and **verifies** an attestation, and your comment names
> the exact failure: the attestation's source digest / builder identity won't match a build-time swap.

---

## Prove the control (your finish line)

**One deterministic finish line: the gate flips.** Build `pipeline-gate.sh` — the executable slice of
the find-half — chaining gitleaks + trivy with independent exit codes, then show it **blocks the
breach-shaped input and passes the clean one:**

1. **Vulnerable → BLOCKED.** Run the gate against the seeded `data/repo` (planted secret) and
   `python:3.8-slim` (EOL, CRITICAL CVEs). It must **exit nonzero** — the deploy is refused.
2. **Clean → passes.** Remove the planted secret (or point at a clean copy) and swap the image to
   `python:3.12-slim`, re-run. It must **exit 0** — the deploy proceeds.

If it doesn't flip, the verdict isn't yet code. The provenance gate in `workflow-hardened.yml` is this
same control's CI peer: the hardened workflow **fails the SolarWinds-shaped build and passes the clean
one.** Score your three README "Call it" predictions against the reveals; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. In `commit → source → build → sign → publish`, where did SUNBURST inject, and why does "bad code in
   the repo" miss?
2. What does a valid code-signing signature prove — and what does it crucially *not*? Name the control
   that fills the gap.
3. Why wouldn't the find-half (gitleaks/trivy/SBOM) have caught SUNBURST, and what *does* each of the
   three scan?

---

## Deliverables

- **`workflow-hardened.yml`** — the hardened, provenance-gated Actions workflow (the portfolio artifact).
- **`pipeline-audit.md`** — the injection-point prediction + reveal, the three-tool findings, and the
  per-issue workflow audit with ATT&CK mappings.
- **`trivy.yaml`** — image-scan policy with at least one accepted-risk exception and a rationale comment.
- **`pipeline-gate.sh`** — the find-half automation that flips (below).

Commit these. Do **not** commit the gitleaks/trivy JSON reports, the SBOM, secrets, or any real
credentials.

## Automate & own it

**Required — the pipeline gate *is* the automation.** Your verdict is "signing proves *who*, not *what* —
provenance is the gate." Encode it two ways that must agree:

- **`pipeline-gate.sh`** — the executable slice you can run today: gitleaks + trivy chained on independent
  exit codes, **failing the seeded secret and the EOL image, passing the clean inputs** (proven above).
- **`workflow-hardened.yml`** — its CI peer: pins every action to a SHA, mints OIDC instead of standing
  secrets, blocks on gitleaks/trivy, and **gates deploy on a verified build-provenance attestation tied
  to the source commit + trusted builder** — the exact hardening this curriculum's repos shipped as **T23.**

Have a model draft the YAML and the script; review every line and confirm the provenance step *actually
gates* (a valid signature alone must not be enough) and that no `${{ }}` reaches a shell unsanitised.
Then adversarially ask the model to write a commit/build that sneaks past your hardened workflow — if it
can, your gate is too narrow.

## Success criteria — you're done when

- [ ] You recorded a *pre-reveal* prediction of the injection point and scored it against the build-step reveal.
- [ ] gitleaks finds the planted secrets (plus your custom `_tok_…` rule) and trivy outputs CVE counts + an SBOM for at least one image.
- [ ] You can state in one sentence **what a signature proves and what it doesn't**, and why the find-half wouldn't have caught SUNBURST.
- [ ] `workflow-hardened.yml` pins all `uses:` to SHAs, uses OIDC (no standing secrets), sets minimal per-job permissions, sanitises expressions, gates on gitleaks + trivy, **and emits + verifies a build-provenance attestation.**
- [ ] `pipeline-gate.sh` **exits nonzero on the seeded secret / EOL image and exits 0 on clean inputs** — the gate flips.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

The image-scan policy and SBOM here feed **Module 10 (Container & Image Security)**, where signing and
attestation get the full treatment. The OIDC-over-secrets move closes the loop with **Module 07
(Secrets Management)** — the pipeline is where "no long-lived creds" becomes concrete. The hardened,
provenance-gated workflow is the **delivery gate of the Phase-1 capstone**: the same workflow that fails
the original breach-shaped config and passes the fixed-as-code system.

## Marketable proof

> "Given a real supply-chain breach (SolarWinds/SUNBURST), I can locate the build-step injection point,
> explain why a valid signature didn't stop it, and deliver a hardened CI/CD workflow that pins actions to
> SHAs, uses OIDC instead of standing secrets, gates on gitleaks + trivy, and **verifies build provenance**
> — the missing control that breaks the chain."

## Stretch

- Wire `actions/attest-build-provenance` in a throwaway public GitHub repo and **verify the attestation**
  with the GitHub CLI on a real build — see the provenance gate fire end to end where the platform
  actually produces it.
- Add a Dependabot config (`package-ecosystem: "github-actions"`) so your SHA pins are bumped via PR and
  don't go stale — the second half of the repo's T23 pattern.
- Re-run `pipeline-gate.sh` as a `pre-commit` hook so the secret scan blocks *before* the push, not only in CI.
