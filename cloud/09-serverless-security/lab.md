# Lab 09 — The Role Is the Blast Radius: Attack a Serverless Function, Then Scope It

*Variant D · breach-driven, attacker→fixer. [← Back to the module concept](README.md)*

> **Hands-on lab.** Environment: `plaintext-labs/cloud/09-serverless-security` (runs on
> [**floci**](https://github.com/floci-io/floci), a free, MIT-licensed local AWS emulator on
> `localhost:4566` — no cloud account, no real credentials; it replaced LocalStack after the CE sunset in
> March 2026). **Objective:** prove a Lambda's blast radius **is its execution role**, land a real
> event-data injection, then least-privilege the role and close the injection. **Target:** ~90 min, one
> finish line: **an over-broad execution role proven, then scoped.**

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Blast radius = the execution role, not the code.** | A 40-line function with `iam:*`/`s3:*` on `*` is account-wide reach. Read the policy, not the line count. |
| 2 | **Code is ephemeral; identity is standing.** | The container vanishes; the admin user / assumed role / exfil'd data it enabled do not. |
| 3 | **Event data is untrusted input crossing a trust boundary.** | An authenticated *source* never makes the payload safe — OWASP Serverless #1. |
| 4 | **Injectable function + over-broad role = confused deputy.** | Your event makes the function act with privileges you never held directly. |
| 5 | **Denonia got in on stolen creds, not a Lambda CVE.** | Provider owns the runtime; the customer owns the role and the input handling. |
| 6 | **The fix has two halves, both verifiable.** | Scope the role (prove with `simulate-principal-policy`) *and* validate event fields in code. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [blast radius, revealed](README.md#the-blast-radius-revealed) and the
> [OWASP Serverless Top 10](https://owasp.org/www-project-serverless-top-10/) (#1 Event-Data Injection).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A 40-line Lambda holds `iam:*` on `*`. Why is its blast radius the whole account, not the function's
   own data?
2. The event arrives from an **authenticated** API Gateway. Why is the JSON body still untrusted — and
   what does an over-broad role turn that injection into?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/09-serverless-security
make up          # start floci + deploy the vulnerable Lambda (over-broad role)
make demo        # worked walkthrough: enumerate role → env vars → normal invoke → injection
make shell       # drop into the lab container (aws + cloudfox + jq)
make down        # stop when done
```

Three focused targets sit under `make demo` if you want to run the beats one at a time:
`make enumerate` (functions + role policy), `make invoke` (normal call), `make inject` (the injection).

**What's real and what isn't — read this before you trust a result.**

- **floci genuinely runs Lambda.** Your `handler.py` executes in a real runtime container (floci launches
  it via the host Docker socket), so the **event injection in Part 2 is real exploitation** — you send a
  payload and the function runs your command, then hands you its output.
- **floci does *not* enforce IAM.** A denied call won't bounce on its own, so you can't prove the role's
  reach by brute-forcing calls. You prove reach the way modules 02–03 did: with
  `aws iam simulate-principal-policy`, which runs AWS's real evaluation logic and returns
  `allowed` / `implicitDeny` / `explicitDeny` *and why*. The injection is **exploited**; the role's blast
  radius and your fix are **assessed from policy logic.**
- **The legitimate data path isn't seeded.** The scoped role's real job (a DynamoDB `PutItem` + an SNS
  `Publish`) has no live table or topic in floci, so you validate that leg the same way — with
  `simulate-principal-policy` against the policy text, not a live call. **Real-AWS caveat:** to watch
  enforcement *live* (a denied `iam:CreateUser` actually erroring, a real `PutItem` succeeding), run the
  identical `aws` steps against **a real AWS account you own** — the lab drives plain `aws` via
  `AWS_ENDPOINT_URL`, so nothing changes but the endpoint.

> **▸ On track if:** `make demo` prints the `notifier` function (`python3.12`), the `NotifierPolicy`
> actions `s3:*` / `iam:*` / `sts:AssumeRole`, the environment variables (`APP_API_KEY`,
> `DB_CONNECTION_STRING`), and — from the injection beat — the `command_output` of `ls /var/task` listing
> the function source. The seeded account is live and the function really runs.

> **Authorization note.** Only test systems you own or have explicit written permission to test.
> Everything here runs locally against a simulated account you own. The injection step executes commands
> inside a function *you* deployed — never run these payloads against a function you do not own.

---

## Scenario

The target account acquired a startup whose payment-notification system is a single Lambda, `notifier`,
triggered by API events. Before connecting the acquired account to the corporate org, you're auditing it —
and you've read the Denonia report, so you know an attacker with a foothold in a Lambda inherits its
role. Your deliverable is a **blast-radius verdict + the fix**: prove how far the execution role reaches,
prove the function is injectable, then least-privilege the role, close the injection, redeploy, and prove
both paths are gone.

Each step runs the same rhythm: **Predict** (commit before you touch anything) → **Do** (gather/exploit
the evidence) → **Reveal** (check your call) → **Record** (one line in the verdict).

---

## Build it — read a little, do a little

### Part 1 — Predict the blast radius, then prove it's the role

#### Step 1 — Read the function, then read the role

**Concept (30 sec):** Flight-card #1. The size of the function tells you nothing; the size of the *role*
tells you everything.

**Predict, then do:** list the function (`aws lambda list-functions`) and read its handler
(`data/lambda/handler.py`) — it's ~40 lines. **Predict from the code alone:** how much damage could a
foothold here do? Now read the execution role's inline policy:
```bash
aws iam get-role-policy --role-name notifier-role --policy-name NotifierPolicy \
  --query 'PolicyDocument.Statement[].Action'
```

> **▸ On track if:** the actions come back as `s3:*`, `iam:*`, and `sts:AssumeRole` (plus a scoped
> `logs:*`). **Record:** the code is 40 lines; the role is the account.

#### Step 2 — Prove the reach with policy logic, not guesses (the heart of it)

**Concept (30 sec):** Flight-card #1 + #2. This is the hop that turns one foothold into an account. floci
won't bounce a denied call, so you prove reach with AWS's evaluator.

**Do it** (in `make shell`):
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::000000000000:role/notifier-role \
  --action-names iam:CreateUser iam:AttachUserPolicy sts:AssumeRole s3:GetObject \
  --resource-arns arn:aws:s3:::sensitive-records/customer-data.csv \
  --query 'EvaluationResults[*].[EvalActionName,EvalDecision]' --output table
```

> **▸ On track if:** every action evaluates **`allowed`** — the role can mint a user, attach a policy,
> assume any role, and read `sensitive-records`. That `allowed` on `iam:CreateUser` **is** the breach:
> code execution → create user → attach `AdministratorAccess` → a standing admin that outlives the
> function (Denonia's natural next move). **Record:** owner = customer (role scope); plane = control→data;
> blast radius = account-wide.

#### Step 3 — Find the standing secret

**Concept (30 sec):** A secret in the environment is readable by anyone with code execution — and Step 4
hands you exactly that.

**Do it:** `aws lambda get-function-configuration --function-name notifier --query Environment.Variables`.

> **▸ On track if:** you see `APP_API_KEY` and `DB_CONNECTION_STRING` in plaintext. **Record:** owner =
> customer; secret in env, not a runtime fetch — blast radius = "every time the function runs," not "one
> call in a log."

### Part 2 — Cross the trust boundary: exploit the event

#### Step 4 — Invoke it normally

**Do it:** `make invoke` (payload `{"account_id":"ACC-001","event_type":"payment"}`).

> **▸ On track if:** the response is `statusCode: 200` with a `processed` body — the function doing its
> real job. This is your baseline before you abuse it.

#### Step 5 — Inject through the event

**Concept (30 sec):** Flight-card #3 + #4. The gateway authenticates the *caller*; it says nothing about
the *data*. The handler pipes a `command` field into `subprocess(shell=True)`.

**Predict:** the source is authenticated — is the payload safe? **Do:** `make inject` (which sends
`{"account_id":"ACC-001","command":"ls /var/task"}`), then, in `make shell`, craft your own to read the
handler and dump the environment:
```bash
aws lambda invoke --function-name notifier \
  --payload '{"account_id":"ACC-001","command":"cat handler.py"}' /tmp/r.json \
  && jq -r '.body' /tmp/r.json | jq -r '.command_output'
aws lambda invoke --function-name notifier \
  --payload '{"account_id":"ACC-001","command":"env"}' /tmp/r.json \
  && jq -r '.body' /tmp/r.json | jq -r '.command_output'
```

> **▸ On track if:** the response `command_output` contains the source of `handler.py` and then the
> environment (`APP_API_KEY=...`, `DB_CONNECTION_STRING=...`). The source was authenticated; the **data**
> never was — OWASP Serverless #1. Combined with Step 2's role, the injected command runs **as the
> function, with the function's role**: a confused deputy. **Record:** owner = customer (input handling);
> plane = the event trust boundary; this is the foothold Denonia needed.

### Part 3 — Fixer: least-privilege the role, close the injection, redeploy

Tracing the reach and landing the injection is the *finding*; **closing both without breaking the
function's real job is the *fix*** — and a serverless fix has two halves, the role and the code.

#### Step 6 — Author the least-privilege role

**Do it:** the function's only legitimate job is to write one record to a specific DynamoDB table and
publish to a specific SNS topic (plus its own CloudWatch Logs). Write `data/least-privilege-policy.json`
to allow **exactly** that — explicit actions, explicit resource ARNs, **no `*` action, no `*` resource**.
This is the minimum cut from module 02, applied to an execution role (see the scoping table in the
module).

#### Step 7 — Prove the cut holds (both directions)

**Do it:** re-run `simulate-principal-policy` against your scoped policy for the dangerous actions **and**
the two legitimate ones:

> **▸ On track if:** `iam:CreateUser`, `s3:GetObject` on `sensitive-records`, and `sts:AssumeRole` on `*`
> now evaluate **`implicitDeny`**, while `dynamodb:PutItem` on the one table and `sns:Publish` on the one
> topic still evaluate **`allowed`**. If a legitimate call flipped to denied, you cut too much; if a
> dangerous one is still allowed, you cut too little. (This is policy-logic assessment — the real-AWS
> caveat from Setup applies to the *live* enforcement of these calls.)

#### Step 8 — Close the injection in code

**Do it:** edit a copy of `handler.py` → `handler-fixed.py`: validate `command` against an explicit
allowlist (reject anything else with an error), **never** shell-execute event input, and **never** return
or log environment variables. Move the API key to a runtime fetch from a secrets store (or, at minimum,
stop emitting it in the response).

#### Step 9 — Redeploy and re-attack

**Do it:** repackage and redeploy the function to floci
(`aws lambda update-function-code --function-name notifier --zip-file fileb:///tmp/notifier.zip`), then
re-run the Step 5 injection payload.

> **▸ On track if:** the injection payload now returns an **error / rejected** response instead of the
> command output — the real (floci-run) function is closed against the real exploit.

---

## Prove the control (your finish line)

**One line to cross: an over-broad execution role, proven and then scoped.** You're done when both hold:

1. **The blast radius is proven, then denied.** `simulate-principal-policy` shows the original
   `notifier-role` `allowed` to `iam:CreateUser` and to read `sensitive-records`; your
   `least-privilege-policy.json` flips both to `implicitDeny` while keeping `dynamodb:PutItem` and
   `sns:Publish` `allowed`.
2. **The guardrail flips.** Your `Automate & own it` check (below) **fails** the original `NotifierPolicy`
   and **passes** the scoped policy. If it doesn't flip, the verdict isn't yet code.

Score your three README "Call it" predictions against the reveals; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why is a tiny Lambda's blast radius the whole account, and what single object decides it?
2. The function runs for 200 ms then vanishes — what survives that ephemerality does *not* protect you from?
3. The event came from an authenticated gateway — why is the JSON body still untrusted, and what does an
   over-broad role turn that injection into?

---

## Deliverables

`blast-radius-verdict.md` — the per-finding verdict (the proven role reach with the simulator output, the
injection demonstration, the env-var finding), each with owner · plane · the breaking change, mapped to
OWASP Serverless and ATT&CK (T1078 Valid Accounts; T1648/T1496 for the miner outcome).
`least-privilege-policy.json` — your scoped execution role that passes the checker. `handler-fixed.py` —
the remediated function. Commit all three. Do **not** commit emulator state, the SAM `.aws-sam/` build
dir, bucket contents, or any real credentials.

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your verdict is "this function's role is its
blast radius, and it's over-broad." Encode that as a **guardrail that fails the bad role and passes the
scoped one**: a small check (`assert_lambda_role_scoped.py`) that, given a Lambda's execution-role policy,
**fails** (exit non-zero) when any statement grants a wildcard action (`iam:*`, `s3:*`, `*`) or
`Resource: "*"` on a sensitive action, or grants `iam:`/`sts:AssumeRole` an over-broad reach — and
**passes** (exit zero) on your least-privilege policy. Run it against both the original `NotifierPolicy`
and your fix and show it flips. Have a model draft the rule (a Checkov-style static check, or a
`simulate-principal-policy` assertion that the role is denied `iam:CreateUser` / `s3:GetObject` on
anything outside its named resources); review every line and confirm it fails the original for the
*right* reason — the role's reach, not an unrelated nit. This is your verdict made un-recurrable, and the
gate a real org would put in CI so no future function ships with `AdministratorAccess` "to tighten later."

## Definition of done (`serverless-security` ✅)

- [ ] `simulate-principal-policy` shows the original role `allowed` to `iam:CreateUser` and to read
  `sensitive-records` — the blast radius is the role, not the function.
- [ ] Your Step 5 injection executed a command inside the function and returned its output (the handler
  source or `env`).
- [ ] `least-privilege-policy.json` denies every dangerous assertion and still allows both
  legitimate-access assertions.
- [ ] The redeployed `handler-fixed.py` rejects the injection payload, and the re-run confirms it.
- [ ] The guardrail fails `NotifierPolicy` and passes the scoped policy.
- [ ] You scored your three "Call it" predictions and can explain all six flight-card facts cold.

## Connects forward

The execution role you enumerated is the same object as the IAM principals from modules 02–03 — a Lambda's
role *is* an attack-path node, and the minimum cut is the same operation. The over-broad role and the
confused-deputy pattern return in module 14, where you'll drive Pacu/stratus-red-team to detonate the
privesc end-to-end and generate the telemetry; module 15 then asks which of those events shows up in
CloudTrail and writes the detection. The "secret in env vs. runtime fetch" thread ties to the secrets
module (07).

## Marketable proof

> "I proved that a serverless function's blast radius is its execution role, not its code: I enumerated an
> over-broad Lambda role, demonstrated an event-injection foothold that ran as the function, then
> least-privileged the role (proven denied via `simulate-principal-policy`), closed the injection, and
> redeployed. I shipped a CI guardrail that fails any Lambda role granting wildcard IAM/S3 and passes the
> scoped one — and I can explain why ephemerality protects the host, not the identity."

## Stretch

- Drive a `pacu` Lambda module against the over-broad role to *actually* create an admin user, then write
  the CloudTrail event sequence a SIEM would fire on — a direct preview of modules 14–15.
- Replicate the Denonia "secret in env" failure end-to-end: move the API key into AWS Secrets Manager (in
  floci), fetch it at runtime, and show the env-var dump no longer leaks it.
