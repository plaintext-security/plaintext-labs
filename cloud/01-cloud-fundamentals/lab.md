# Lab 01 — Render the Verdict: reproduce a real breach's responsibility chain

> **Hands-on lab.** Environment: `plaintext-labs/cloud/01-cloud-fundamentals` (runs on **floci**, a free
> local AWS emulator — no cloud account). Objective: **render a per-hop responsibility verdict on the
> Capital One chain and encode the fix as a CI guardrail.** Target: **~90 min**, one finish line.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The line runs *through* a service, not between services.** | AWS owns the mechanism; you own its configuration. Judge each control on that split. |
| 2 | **Encryption at rest is silent against an authorized principal.** | The reads decrypt transparently — the failed control was **identity**, not crypto. |
| 3 | **Over-broad IAM turned one foothold into 100M records.** | `s3:*` on `*` for a server role = control-plane failure bleeding into the data plane. |
| 4 | **The metadata service is AWS's; enforcing IMDSv2 + scoping the role is yours.** | Provider mechanism, customer configuration — same feature, your side of the line. |
| 5 | **CloudTrail records; the customer detects.** | A trail with no alert is a customer gap, not a provider one. |
| 6 | **Across all five hops, zero were Amazon's.** | "The default is not secure" — breaches that *look* like provider failures are customer settings. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [model, revealed](README.md#the-model-revealed).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. The Capital One data was **encrypted at rest** and still read in plaintext. Which control actually
   failed — and why did encryption do nothing?
2. The stolen credentials came from **AWS's** metadata service. Name the two settings that made this
   hop the *customer's* failure.

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/01-cloud-fundamentals
make up      # floci + seed an account shaped like the breach
make demo    # enumeration walkthrough
```

**What this lab is — and isn't.** You are **not** re-exploiting Capital One (no SSRF, no live metadata
service). floci does **not enforce** IAM, so a denied call won't bounce on its own — the skill here is
**judgment**, not exploitation. You reproduce the *responsibility conditions* of two hops and, where
enforcement can't be shown live, reason with `aws iam simulate-principal-policy`, which evaluates AWS's
real policy logic (`allowed`/`denied` + why). Because the lab drives plain `aws` via `AWS_ENDPOINT_URL`,
the identical steps later run against a **real AWS account you own** to watch enforcement live.

> **▸ On track if:** `make demo` prints `dev-alice`, the `DevPolicy` document (with `s3:*` / `Resource: "*"`),
> and the `EC2InstanceRole` trust policy — the seeded account is live.

> **Authorization note.** Only test systems you own or have written permission to test. Everything here
> runs locally against a simulated account you own.

---

## Scenario

You're the post-incident analyst. A mid-size finance company has realized their account is shaped
exactly like Capital One's: a server role that can read every bucket, encryption-at-rest on, and
CloudTrail running with nobody watching. Your deliverable is a **verdict memo** — the artifact a real
cloud-IR/GRC analyst writes: per hop, the owner of the failed control, its plane, and the one change
that breaks the chain. Each step runs the same rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Step 1 — Hop 2: the metadata service handed out credentials

**Concept (30 sec):** Flight-card #4. The mechanism is Amazon's; *enforcing IMDSv2* and *scoping the
role's power* are instance/identity settings you own.

**Predict, then do:** write your verdict (provider or customer?), then inspect the role:
`aws iam get-role --role-name EC2InstanceRole --query Role.AssumeRolePolicyDocument`.

> **▸ On track if:** the trust policy returns, and you can state that **nothing here scopes how powerful
> the role is** — that's a customer setting, not something AWS turns on. **Record:** owner = customer;
> plane = control; fix = require IMDSv2 + least-privilege the role.

### Step 2 — Hop 3: the role could read *every* bucket (the heart of it)

**Concept (30 sec):** Flight-card #3. This is the hop that turned one server into 100M records. Prove
the blast radius with policy logic, not exploitation.

**Do it:** confirm `DevPolicy` grants `s3:*` on `*`, create an unrelated bucket, then ask AWS's evaluator
whether the role can read it:
```bash
aws s3api create-bucket --bucket payroll-prod
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::000000000000:role/EC2InstanceRole \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::uploads-dev/x arn:aws:s3:::payroll-prod/x \
  --query 'EvaluationResults[*].[EvalResourceName,EvalDecision]' --output table
```

> **▸ On track if:** **both** resources evaluate `allowed` — the role can read a bucket it has no
> business touching. That `allowed` on `payroll-prod` **is** the breach. **Record:** owner = customer;
> plane = control→data; fix = scope the resource to the one bucket.

### Step 3 — Hop 4: the data was encrypted, and it didn't matter

**Concept (30 sec):** Flight-card #2. An authorized principal's reads decrypt transparently.

**Do it:** check the bucket's encryption (`aws s3api get-bucket-encryption --bucket uploads-dev`, or note
its absence and reason about the *on* case), then re-read Step 2: the role was **authorized**.

> **▸ On track if:** you can state in one line that encryption-at-rest never engages against an
> authorized principal — it defends against stolen media, not over-broad identity. **Record:** owner =
> customer (identity scope, not encryption); plane = data; fix = least-privilege + scope who uses the key.

### Step 4 — Hop 5: it was all in the logs; nobody looked

**Do it:** note that CloudTrail *records* API calls but nothing alerts on "a role listed every bucket."

> **▸ On track if:** your verdict is **owner = customer; plane = detective; fix = an alert on anomalous
> `s3:List*`/cross-bucket access.** AWS records; the customer detects.

---

## Prove the control (your finish line)

Two artifacts, re-checked against the honesty bar:

1. **`verdict-memo.md`** — a row per hop (owner · plane · breaking change) + a two-sentence CISO bottom
   line. Confirm the tally: **zero hops were Amazon's.**
2. **The guardrail flips** — your `Automate & own it` rule (below) **fails** the broken `DevPolicy` and
   **passes** the scoped version. If it doesn't flip, the verdict isn't yet code.

Score your three README "Call it" predictions against the reveals; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why didn't encryption-at-rest stop the exfiltration, and what control actually failed?
2. The metadata service is AWS's — name the two customer settings that made hop 2 the customer's failure.
3. How many of the five hops were Amazon's, and what does that tell you about "provider-looking" breaches?

---

## Deliverables

- **`verdict-memo.md`** — the per-hop responsibility finding (a genuine cloud-IR/GRC artifact; write it
  like one). *Do not commit credentials, the test buckets' contents, or any real account data.*

## Automate & own it

**Required — turn your hop-3 judgment into a guardrail.** Write the control that would have caught Capital
One in CI: a small policy-as-code check (OPA/Rego or Checkov-style, or a `simulate-principal-policy`
assertion) that **fails** any IAM policy granting `s3:*` or `Resource: "*"` to an instance role and
**passes** the scoped version. Run it against both `DevPolicy` and your fix and show it flips. Have a
model draft the rule; you confirm it fails the bad policy for the *right* reason. Judgment-as-code — a
direct preview of module 06 (IaC Security).

## Definition of done (`cloud-fundamentals` ✅)

- [ ] `simulate-principal-policy` shows the role `allowed` to read a bucket it has no business touching (hop 3 reproduced).
- [ ] `verdict-memo.md` has owner + plane + breaking change for all four assessed hops.
- [ ] You conclude **zero hops were the provider's** and can explain the encryption and metadata ones in one sentence each.
- [ ] The guardrail fails `DevPolicy` and passes the scoped policy.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

Every hop is a later module: over-broad role → **IAM attack paths (03)** + **posture auditing (05)**; the
guardrail → **IaC security (06)**; "encrypt but scope the key" → **KMS/data protection (17)**; "logged but
not detected" → **cloud logging & detection (15)** + **incident response (16)**. This memo is the map of
the whole track, drawn from one real breach.

## Marketable proof

> "Given a real cloud breach chain, I can render a per-hop responsibility verdict — owner, plane, and the
> control that breaks the chain — and encode the fix as a CI guardrail. I can explain why encryption-at-rest
> didn't help and why the metadata service wasn't AWS's fault."

## Stretch

- Re-render the verdict for a *different* real cloud breach (a public S3-exposure post-mortem, or a
  documented CloudGoat scenario) and compare which hops, if any, shift to the provider's side.
- Extend the guardrail to also fail a role that doesn't enforce IMDSv2 — closing hop 2 in code too.
