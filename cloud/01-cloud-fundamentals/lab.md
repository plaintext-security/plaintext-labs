# Lab 01 — Render the Verdict: Reproducing a Real Breach's Responsibility Chain

*Variant D · breach-driven, interleaved. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[LocalStack](https://localstack.cloud/) to simulate AWS locally — no cloud account or real credentials
required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/01-cloud-fundamentals
make up         # start LocalStack + seed an account shaped like the breach
make shell      # drop into the lab container
make down       # stop when done
```

**What this lab is — and isn't (read this).** You are **not** re-exploiting Capital One. There is no
SSRF, no live metadata service — and LocalStack does not *enforce* IAM, so a denied call won't bounce
on its own. That's fine, because the skill here isn't exploitation; it's **judgment.** You'll reproduce
the *responsibility conditions* of two hops in a local account and, where enforcement can't be shown
live, reason about it with `awslocal iam simulate-principal-policy`, which evaluates AWS's real policy
logic and tells you `allowed`/`denied` and *why*. Honest tools, honest answer.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against a simulated account you own.

## Scenario
You're the post-incident analyst. The chain from the module brief is on your desk, and a finance company
(call it ) has just realized their account is shaped exactly like Capital One's was: a server
role that can read every bucket, encryption-at-rest switched on, and CloudTrail running with nobody
watching. Your deliverable is a **verdict memo** — the artifact a real cloud-IR or GRC analyst writes:
for each hop, the owner of the failed control, its plane, and the one change that breaks the chain there.

Each step below runs the same rhythm: **Predict** (commit to a verdict *before* touching anything) →
**Do** (gather the evidence) → **Reveal** (check your call) → **Record** (one line in the memo).

## Do

1. [ ] **Hop 2 — metadata handed out credentials.**
   **Predict:** the metadata service is an AWS feature. Write your verdict now: provider or customer?
   **Do:** inspect the EC2 instance role and its trust
   (`awslocal iam get-role --role-name EC2InstanceRole`). Note that nothing scopes how powerful
   the role is, and that *enforcing IMDSv2* is an instance setting, not something AWS turns on for you.
   **Reveal:** the mechanism is Amazon's; **enforcing IMDSv2 and scoping the role are the customer's** —
   the line runs *through* the feature. **Record:** owner = customer; plane = control; breaking change =
   require IMDSv2 + least-privilege the role.

2. [ ] **Hop 3 — the role could read *every* bucket.**
   **Predict:** an app server's role should reach only its own bucket. Will this one?
   **Do:** this is the heart of the breach — reproduce it. Confirm the role's policy
   (`DevPolicy`) grants `s3:*` on `*`, then prove the blast radius with
   `awslocal iam simulate-principal-policy`: ask whether the role can `s3:GetObject` on
   `uploads-dev` **and** on a second, unrelated bucket you create
   (`awslocal s3api create-bucket --bucket payroll-prod`). Both come back `allowed`.
   **Reveal:** over-broad IAM is the customer control that turned one foothold into 100M records —
   identity (control plane) failing *into* data access (data plane). **Record:** owner = customer;
   plane = control→data; breaking change = scope the resource to the one bucket.

3. [ ] **Hop 4 — the data was encrypted, and it didn't matter.**
   **Predict:** server-side encryption was on. Did it stop the exfiltration?
   **Do:** check the bucket's encryption (`awslocal s3api get-bucket-encryption` — or note its absence
   and reason about the on case). Then re-read your hop-3 result: the role was *authorized*.
   **Reveal:** an authorized principal's reads are decrypted transparently — encryption-at-rest never
   engages. It defends against stolen media, not over-broad identity. **Record:** owner = customer
   (the identity scope, not the encryption); plane = data; breaking change = least-privilege + scope
   who can use the key (you'll go deep on this in the KMS module).

4. [ ] **Hop 5 — it was all in the logs; nobody looked.**
   **Predict:** CloudTrail was on. Whose job was it to catch this?
   **Do:** confirm the account *has* an audit trail concept (CloudTrail records API calls); note there's
   no alerting wired to "a role listed every bucket." **Reveal:** AWS *records*; the customer *detects*.
   A trail with no detection is a customer gap, not a provider one. **Record:** owner = customer; plane =
   detective; breaking change = an alert on anomalous `s3:List*`/cross-bucket access (your Track-02 and
   module-15 skill).

5. [ ] **Tally and render.** Count the verdicts. Confirm what the module predicted: **zero hops were
   Amazon's.** Write the memo: a row per hop (owner · plane · breaking change) and a two-sentence
   bottom line a CISO could read.

## Success criteria — you're done when
- [ ] You've reproduced hop 3 concretely: `simulate-principal-policy` shows the role `allowed` to read a
  bucket it has no business touching.
- [ ] Your `verdict-memo.md` has a verdict for all four reproduced/assessed hops, each with owner +
  plane + the one breaking change.
- [ ] You correctly conclude **zero hops were the provider's**, and can explain the two that most people
  get wrong (encryption, metadata) in one sentence each.
- [ ] You scored your three "Call it" predictions from the README against the reveals and noted which you
  missed.

## Deliverables
`verdict-memo.md` — the per-hop responsibility finding. This is a genuine cloud-IR/GRC artifact, not a
worksheet; write it like one. Commit it alongside the seed data. Do not commit credentials, the test
buckets' contents, or any real account data.

## Automate & own it
**Required — but not the usual "script your keystrokes."** Your verdict on hop 3 is a *judgment*; turn it
into a **guardrail.** Write the control that would have caught Capital One in CI: a small policy-as-code
check (an OPA/Rego or Checkov-style rule, or a `simulate-principal-policy` assertion in a script) that
**fails** any IAM policy granting `s3:*` or `Resource: "*"` to an instance role, and **passes** the
scoped version. Run it against both the broken `DevPolicy` and your fixed policy and show it
flips. Have a model draft the rule; you review every line and confirm it fails the bad policy for the
*right* reason. This is judgment-as-code — your verdict, encoded so it can never silently recur — and a
direct preview of module 06 (IaC Security).

## AI acceleration
Before writing your memo, ask a model to render the per-hop verdict from the public post-mortem, then
audit it. It will likely claim the encryption protected the data (hop 4 — false) and drift toward
blaming the AWS metadata service (hop 2 — wrong owner). Catching and correcting those two is the entire
skill. Paste your guardrail rule in too and ask it to find a policy that sneaks past — if it can, your
rule is too narrow.

## Connects forward
Every hop you verdicted is a later module: the over-broad role → IAM attack paths (03) and posture
auditing (05); the guardrail you wrote → IaC security (06); "encrypt but scope the key" → the KMS/data-
protection work; "logged but not detected" → cloud logging & detection (15) and incident response (16).
This memo is the map of the whole track, drawn from one real breach.

## Marketable proof
> "Given a real cloud breach chain, I can render a per-hop responsibility verdict — owner, plane, and the
> control that breaks the chain — and encode the fix as a CI guardrail. I can explain why encryption-at-
> rest didn't help and why the metadata service wasn't AWS's fault."

## Stretch
- Re-render the verdict for a *different* real cloud breach (e.g. a public S3-exposure post-mortem from
  the [CSA breach database](https://cloudsecurityalliance.org/) or a documented CloudGoat scenario) and
  compare which hops shift to the provider's side, if any.
- Extend your guardrail to also fail a role that doesn't enforce IMDSv2, closing hop 2 in code too.
