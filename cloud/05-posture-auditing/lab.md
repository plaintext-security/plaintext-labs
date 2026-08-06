# Lab 05 — Audit, Triage, Remediate, Verify: Find the 2017 Bucket Before a Researcher Does

> **Hands-on lab.** Environment: `plaintext-labs/cloud/05-posture-auditing` (runs on **floci**, a free
> local AWS emulator — no cloud account). Objective: **audit a seeded account with `prowler`, triage the
> dump to the finding that matters, remediate it, re-scan to prove FAIL→PASS, and freeze that verdict as a
> guardrail.** Target: **~2 hrs**, one finish line. [← Back to the module concept](README.md)

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **A posture scanner is a linter for your account.** | `prowler` walks every resource and prints CIS-rule violations. Running it is *one command* — the value is what you do next. |
| 2 | **Misconfiguration, not vulnerability, is the dominant cloud breach cause.** | The 2017 S3 wave was one ACL at scale. A scanner finds it in seconds; nobody acted. |
| 3 | **Triage = severity × exploitability × blast radius**, with asset context the tool can't have. | The raw finding count is *not* the priority order. A MEDIUM on a sandbox is noise; a public bucket with PII is the 2017 leak. |
| 4 | **Map each finding to its CIS control and the ATT&CK it enables.** | Public bucket → **T1530**; stale/over-broad key → **T1078**. The technique is the blast radius the severity stamp hides. |
| 5 | **Remediation isn't done until re-scan proves FAIL→PASS.** | A fix you didn't re-scan is a wish. That flip is the deliverable — and the seed of the guardrail. |
| 6 | **Suppression is a conscious, documented decision** — never the default way to clear a finding. | Closing all 400 or silencing the noisy rule are both wrong. Write the rationale or don't suppress. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) and the UpGuard 2017 writeups in
> [Go deeper](README.md#go-deeper-4-hrs--optional).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A first scan of a year-old account returns hundreds of findings. What single move turns that dump into
   a triage queue — and why is the raw count the *wrong* way to prioritise?
2. The scanner stamps the public bucket **MEDIUM**. What account-specific fact would override that
   severity, and why can't the tool know it?

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs
[floci](https://github.com/floci-io/floci) (a free, MIT-licensed local AWS API emulator) and a lab
container with `prowler` pinned — no cloud account or real credentials required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/05-posture-auditing
make up      # start floci + seed a deliberately misconfigured account
make demo    # run prowler and show the HIGH/CRITICAL findings
make shell   # drop into the lab container (prowler + aws + jq)
make down    # stop when done
```

`make up` seeds the inherited account with the exact shapes from the case: a **public S3 bucket with a
file in it** (`inherited-public-data`, the 2017 wave), a security group open to `0.0.0.0/0` on 22/3389
(`wide-open`), an IAM access key that was never rotated (`svc-legacy`), and a CloudTrail trail that
exists but isn't logging (`trail`).

> **▸ On track if:** `make up` finishes with the summary block listing all five —
> `inherited-public-data (public ACL)`, the `wide-open` SG on `22, 3389`, `svc-legacy (stale access
> key)`, `trail (logging disabled)`, and root MFA disabled. If you see those, the account is live.

**What this lab is — and isn't (read this).** floci emulates the AWS *API surface* `prowler` reads, so
the findings are real findings against real config. It does **not** reproduce the 2017 exfiltration
(there's no public internet pointing at the bucket) — you're not stealing data, you're doing the audit
that would have caught it. `prowler` reads the emulator endpoint from `AWS_ENDPOINT_URL`
(`http://floci:4566`, already set in the container), so inside the shell you just run `prowler aws`.

> **The real-AWS caveat.** A few CIS checks depend on account state floci does not model — e.g. **root
> MFA** (CIS 1.5) and IAM credential-report timing. Treat those as *assessed from config*, not exploited.
> Because the lab drives plain `prowler`/`aws` against an endpoint, the **identical** commands run against
> a **real AWS account you own** to see those checks resolve for real.

> **Authorization note.** Only audit accounts you own or have explicit written permission to test.
> Posture tools touch every resource; never point them at a tenant that isn't yours. Everything here is a
> local account you own.

---

## Scenario

Your org just acquired a startup and inherited its AWS account — never formally reviewed. You must
produce a first-pass posture report **before it's connected to the corporate network.** The account is
shaped like 2017: a public bucket sits in it right now. Your deliverable is a triaged finding list mapped
to CIS, a remediation that you **apply and verify**, and a guardrail that keeps the worst finding from
ever passing review again. Each step runs the same rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Step 1 — Inventory before you scan (build the context the tool lacks)

**Concept (30 sec):** Flight-card #3. The scanner supplies findings; *you* supply which resource holds
what. That asset context is the part no scanner can run — so gather it first.

**Predict, then do:** guess which resource is the 2017 bucket, then from `make shell` list what's
actually in the account by eye:

```bash
aws s3 ls
aws s3api get-bucket-acl --bucket inherited-public-data
aws ec2 describe-security-groups --query 'SecurityGroups[?GroupName==`wide-open`]'
aws iam list-users
```

> **▸ On track if:** `aws s3 ls` shows `inherited-public-data`, its ACL grants `READ` to the
> `AllUsers` group (`http://acs.amazonaws.com/groups/global/AllUsers`), and the SG lists `0.0.0.0/0` on
> ports 22 and 3389. **Record:** the public bucket holds `employee-list.csv` (PII) — that fact outranks
> whatever severity the tool later prints.

### Step 2 — Run the linter (the "many findings, one verdict" gap)

**Concept (30 sec):** Flight-card #1. One command; the output is the *start* of the work.

**Predict, then do:** predict the FAIL count, then run the scan and write JSON:

```bash
prowler aws --services s3 ec2 iam cloudtrail \
  --output-formats json-ocsf --output-directory /tmp/prowler-out
jq '[.[]|select(.status_code=="FAIL")]|length' /tmp/prowler-out/*.ocsf.json
```

> **▸ On track if:** `prowler` completes and the FAIL count is **≥ 5** — more findings than the *one*
> that matters. That gap is the module. (`make demo` prints the HIGH/CRITICAL subset and the line
> `Total HIGH/CRITICAL FAIL findings: N` if you want the scoped view first.) On a real year-old account
> this number is in the *hundreds* — same skill, more noise.

### Step 3 — Triage to the top five, mapped to CIS + ATT&CK

**Concept (30 sec):** Flight-card #3 and #4. Rank by *your* judgment, not the tool's order.

**Do it:** pull the failing checks, then for your top five record check ID (`finding_info.uid`), the
resource ARN, the prowler severity, the **CIS control**, and the **ATT&CK technique it enables**:

```bash
jq -r '.[]|select(.status_code=="FAIL")
        |[.severity,.finding_info.uid,(.resources[0].uid//.resources[0].name)]|@tsv' \
  /tmp/prowler-out/*.ocsf.json
```

Then override the tool's order: the public bucket with PII → **top**, regardless of its stamped severity;
map it to **T1530** (Data from Cloud Storage) and the stale key to **T1078** (Valid Accounts).

> **▸ On track if:** the S3 public-access finding on `inherited-public-data` is in your list (check id
> `s3_bucket_public_access`),
> and you can state in one line why it outranks `svc-legacy`'s stale key *even if the tool labelled them
> the same*. **Record:** the top-five table (this is `findings-summary.md`).

### Step 4 — Confirm the headline finding by hand

**Concept (30 sec):** Verify `prowler` wasn't lying — this is the literal Accenture/Verizon/INSCOM
condition.

**Do it:** read the ACL and the public-access block, and confirm the object reads:

```bash
aws s3api get-public-access-block --bucket inherited-public-data
aws s3 cp s3://inherited-public-data/employee-list.csv - | head
```

> **▸ On track if:** `get-public-access-block` shows all four flags `false` (or the call errors "no
> configuration" — same meaning: nothing is blocking public access), and the CSV's `employee_id,name,...`
> rows print. You've now confirmed the 2017 condition from config, not just from the tool.

### Step 5 — Remediate and re-scan — prove FAIL→PASS

**Concept (30 sec):** Flight-card #5. A remediation you didn't re-scan is a wish. This flip is the
deliverable.

**Do it:** re-enable block-public-access and drop the public ACL, then **re-run that one check**:

```bash
aws s3api put-public-access-block --bucket inherited-public-data \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-acl --bucket inherited-public-data --acl private
prowler aws --check s3_bucket_public_access
```

> **▸ On track if:** the re-scan of that single check now reports **PASS** for `inherited-public-data`,
> and `aws s3 cp s3://inherited-public-data/employee-list.csv -` from an unauthenticated context would no
> longer be reachable. That FAIL→PASS flip is your before/after evidence. **Record:** `remediation-notes.md`.

### Step 6 — (Stretch) Second opinion

**Do it:** run ScoutSuite against the same account (`scout aws`) and diff its findings against prowler's —
where they agree, and what each catches that the other misses (two linters, different blind spots).

---

## Prove the control (your finish line)

One flip, verified against the honesty bar:

1. **`findings-summary.md`** — the triaged top-five table (check ID · resource · severity · CIS control ·
   ATT&CK · your re-ranked priority + one-line rationale · owner), with the public bucket at the top and a
   sentence saying *why* it outranks the stale key regardless of the tool's severity.
2. **The finding flips** — you **applied one remediation and re-ran that check FAIL→PASS**, and your
   `Automate & own it` guardrail (below) **fails** the broken account and **passes** the fixed one, mapped
   to its CIS control. If the guardrail doesn't flip, the verdict isn't yet code.

Score your two warm-up predictions against what you found; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. What turns a hundred-line finding dump into a triage queue, and why is the raw count the wrong order?
2. The scanner stamped the public bucket a middling severity — what fact overrides it, and why can't the
   tool know it?
3. Your plan says "fix the public bucket." What single step proves it's actually done, and how does that
   step become the guardrail?

---

## Success criteria — you're done when

- [ ] `prowler` completes and returns at least five FAIL findings against the seeded account.
- [ ] Your top-five list is triaged — check ID, ARN, severity, CIS control, ATT&CK technique — and
  **re-ordered by your own blast-radius judgment** with a one-line rationale per finding.
- [ ] You verified the public-bucket finding **by hand** (read the object / inspected the ACL), not just
  from prowler's output.
- [ ] You **applied one remediation and re-scanned**, showing that check flip FAIL→PASS.
- [ ] Your guardrail **fails** the broken account and **passes** the fixed one, mapped to its CIS control.

---

## Deliverables

Commit to your **portfolio** repo (not `plaintext-labs`):

- `findings-summary.md` — the triaged top-five table (check ID · resource · severity · CIS control ·
  ATT&CK · your re-ranked priority + rationale · owner).
- `remediation-notes.md` — the plan, plus the before/after evidence of the one finding you flipped
  FAIL→PASS.
- `check_public_bucket.py` (or `.sh`) — the guardrail from **Automate & own it**.

Do **not** commit: the full prowler JSON (too large), any emulator state, `/tmp/legacy-key.json`, or any
`*.key`/`*.pem`/real-key-pattern file.

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your verdict is "no bucket in this account may
be publicly readable" — the exact control whose absence *was* the 2017 wave. Encode it as a **benchmark
check that fails the bad state and passes the fix**, mapped to its CIS control. Write
`check_public_bucket.py` (or a small shell check) that, given the account, **fails (exit non-zero)** if
any bucket has public ACLs or block-public-access disabled — printing the bucket and the control it
violates, e.g. **CIS AWS 2.1.x — "Ensure S3 buckets are not publicly accessible"** — and **passes (exit zero)** once you've
remediated. Run it against the seeded account (red), apply your fix, and run it again (green). Have a
model draft the boto3/`aws` calls and the assertion; review every line and confirm it fails for the
*right* reason (the public ACL, not an unrelated bucket). This is your triage verdict made un-recurrable —
and in module 06 you'll lift this exact check into a CI gate that blocks the merge before the bucket ever
ships.

## Definition of done (`posture-auditing` ✅)

- [ ] `make up` seeded the five misconfigs and `prowler` returns ≥ 5 FAIL findings.
- [ ] `findings-summary.md` has check ID + ARN + severity + CIS control + ATT&CK + re-ranked priority for
  the top five, public bucket at the top.
- [ ] You confirmed the public-bucket condition **by hand** and can explain the real-AWS caveat (root MFA
  is assessed-from-config).
- [ ] `remediation-notes.md` shows one finding flipped **FAIL→PASS** on re-scan.
- [ ] The guardrail fails the broken account and passes the fixed one, mapped to its CIS control.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

Every finding here is a later module. The over-broad grants tie back to **02 (IAM)** and the public-bucket
verdict is the same one you rendered in **01**. The guardrail you wrote is lifted, almost verbatim, into
the CI gate of **06 (IaC Security)** — where it blocks the misconfiguration *before* deploy, not after. And
when an attacker actually exploits a posture gap like this, **15 (Logging & Detection)** is where you write
the detection for it.

## Marketable proof

> "I ran an automated CIS-benchmark audit against a cloud account, triaged a noisy finding set down to the
> few that mattered by blast radius (not raw count), remediated the worst and **re-scanned to prove the fix
> held**, and encoded that verdict as a benchmark guardrail — mapped to its CIS control — that fails the
> misconfiguration and passes the fix. I can explain why the 2017 S3 wave was one ACL at scale."

## Stretch

- Add a `--baseline` mode to your guardrail that loads a prior scan and reports only **new** findings — the
  delta-scan pattern of continuous posture monitoring.
- Extend the guardrail to a second 2017-class control (e.g. no `0.0.0.0/0` on sensitive ports), so it
  covers the `wide-open` security-group finding too — a direct preview of module 04's network guardrail.
- Run ScoutSuite against the same account and diff its findings against prowler's — two linters, different
  blind spots.
