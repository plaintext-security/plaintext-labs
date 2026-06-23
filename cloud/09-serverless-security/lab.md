# Lab 09 — The Role Is the Blast Radius: Attack a Serverless Function, Then Scope It

*Variant D · breach-driven, attacker→fixer. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[LocalStack](https://localstack.cloud/) to simulate AWS locally — no cloud account or real credentials.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/09-serverless-security
make up          # start LocalStack + deploy the vulnerable Lambda (over-broad role)
make demo        # worked walkthrough: enumerate role → normal invoke → event injection
make shell       # drop into the lab container (awslocal + cloudfox)
make down        # stop when done
```

**What's real and what isn't (read this).** **LocalStack genuinely runs Lambda** — your function code
actually executes in a container, so the **event injection in Part 2 is a real exploitation**, not a
simulation: you send a payload and the function runs your command. Where LocalStack is *honest about its
limits* is **IAM enforcement** — LocalStack CE does **not** enforce IAM, so the role's reach can't be
proven by brute-forcing denied calls. You prove reach the same way module 02 did: with
`awslocal iam simulate-principal-policy`, which runs AWS's real evaluation logic and returns
`allowed` / `implicitDeny` / `explicitDeny` *and why*. So the injection is *exploited*; the role's blast
radius and your fix are *assessed from policy logic.* Honest tools, honest claims.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against a simulated account you own. The injection step executes commands inside a function *you*
> deployed — never run these payloads against a function you do not own.

## Scenario
The target account acquired a startup whose payment-notification system is a single Lambda,
`notifier`, triggered by API events. Before connecting the acquired account to the corporate
org, you're auditing it — and you've read the Denonia report, so you know an attacker with a foothold in
a Lambda inherits its role. Your deliverable is a **blast-radius verdict + the fix**: prove how far the
execution role reaches, prove the function is injectable, then least-privilege the role, close the
injection, redeploy, and prove both paths are gone.

Each step runs the same rhythm: **Predict** (commit before you touch anything) → **Do** (gather/exploit
the evidence) → **Reveal** (check your call) → **Record** (one line in the report).

## Do

### Part 1 — Predict the blast radius, then prove it's the role

1. [ ] **Look at the function, then the role.** List the function
   (`awslocal lambda list-functions`) and read its handler (`data/lambda/handler.py`) — it's ~40 lines.
   **Predict** from the code alone: how much damage could a foothold here do? Now read the execution
   role's policy (`awslocal iam get-role-policy --role-name notifier-role --policy-name NotifierPolicy`).
   **Reveal:** `s3:*`, `iam:*`, and `sts:AssumeRole` all on `*`. **Record:** the code is 40 lines; the
   role is the account.

2. [ ] **Prove the reach with policy logic — not guesses.** Use
   `awslocal iam simulate-principal-policy` (or `cloudfox`'s permissions/iam-simulator) against the role
   to confirm it is `allowed` to `iam:CreateUser`, `iam:AttachUserPolicy`, and `s3:GetObject` on the
   seeded `sensitive-records` bucket. **Reveal:** this is Denonia's natural next move — code
   execution → `iam:CreateUser` + attach `AdministratorAccess` → standing admin that outlives the
   function. **Record:** owner = customer (role scope); the function's blast radius is account-wide.

3. [ ] **Find the standing secret.** Read the function configuration
   (`awslocal lambda get-function-configuration --function-name notifier`). What's in the
   environment variables? **Reveal:** a fake API key and a DB connection string — readable in one call by
   anyone with code execution (the next step gives you exactly that). **Record:** owner = customer; secret
   in env, not a runtime fetch — blast radius = "whenever the function runs," not "one call with a log."

### Part 2 — Cross the trust boundary: exploit the event

4. [ ] **Invoke it normally.** Send a well-formed payload
   (`{"account_id":"ACC-001","event_type":"payment"}`) and read the response. This is the function doing
   its job.

5. [ ] **Inject through the event.** **Predict:** the function is fronted by an authenticated gateway —
   is the JSON payload safe? **Do:** the handler passes a `command` field to a subprocess. Craft a payload
   (`{"account_id":"ACC-001","command":"ls /var/task"}`, then `cat` the handler, then `env`) and read the
   output back through the response. **Reveal:** the source was authenticated; the *data* never was — this
   is OWASP Serverless #1, and combined with step 2's role it's a confused deputy. The injected command
   runs **as the function**, with the function's role. **Record:** owner = customer (input handling);
   plane = the event trust boundary; this is the foothold Denonia needed.

### Part 3 — Fixer: least-privilege the role, close the injection, redeploy

Tracing the reach and landing the injection is the finding; **closing both without breaking the
function's real job is the fix** — and a serverless fix has two halves, the role and the code.

6. [ ] **Author the least-privilege role.** The function's only legitimate job is: write one record to a
   specific DynamoDB table and publish to a specific SNS topic (plus its own CloudWatch Logs). Edit
   `data/least-privilege-policy.json` to allow **exactly** that — explicit actions, explicit resource
   ARNs, no `*` action, no `*` resource. This is the minimum cut from module 02, applied to an execution
   role.

7. [ ] **Prove the role cut holds.** Run `make check-role` (a `simulate-principal-policy` harness): the
   dangerous assertions (`iam:CreateUser`, `s3:GetObject` on the sensitive bucket, `sts:AssumeRole` on
   `*`) must now return `implicitDeny`/`explicitDeny`, while the two legitimate ones (the DynamoDB
   `PutItem` and the SNS `Publish`) still return `allowed`. If a legitimate call flipped to denied, you
   cut too much.

8. [ ] **Close the injection in code.** Edit a copy of `handler.py`: validate `command` against an
   explicit allowlist (reject anything else with an error), never shell-execute event input, and never
   return or log environment variables. Move the API key to a runtime fetch from a secrets store (or at
   minimum, stop emitting it).

9. [ ] **Redeploy and re-attack.** Repackage and redeploy the function to LocalStack, then re-run the
   step-5 injection payload. **Confirm it now returns an error** instead of executing the command — the
   real exploit, now closed against the real (LocalStack-run) function.

## Success criteria — you're done when
- [ ] `simulate-principal-policy` shows the original role `allowed` to `iam:CreateUser` and read the
  sensitive bucket — you've proven the blast radius is the role, not the function.
- [ ] Your event-injection payload (step 5) executed a command inside the function and returned its output
  (e.g. the handler source or `env`).
- [ ] `least-privilege-policy.json` passes `make check-role`: every dangerous assertion now **denies**,
  both legitimate-access assertions still **allow**.
- [ ] The redeployed `handler.py` rejects the injection payload, and the re-run confirms it.
- [ ] You scored your three "Call it" predictions from the README against the reveals.

## Deliverables
`blast-radius-verdict.md` — the per-finding verdict (the proven role reach with the simulator output, the
injection demonstration, the env-var finding), each with owner · plane · the breaking change, mapped to
OWASP Serverless and ATT&CK (T1078 Valid Accounts, T1648/T1496 for the miner outcome). `least-privilege-policy.json`
— your scoped execution role that passes the checker. `handler-fixed.py` — the remediated function. Commit
all three. Do **not** commit LocalStack state, the SAM `.aws-sam/` build dir, bucket contents, or any real
credentials.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your verdict is "this function's role is its
blast radius, and it's over-broad." Encode that as a **guardrail that fails the bad role and passes the
scoped one**: a small check (`assert_lambda_role_scoped.py`) that, given a Lambda's execution-role policy,
**fails** (exit non-zero) when any statement grants a wildcard action (`iam:*`, `s3:*`, `*`) or
`Resource: "*"` on a sensitive action, or grants `iam:`/`sts:AssumeRole` an over-broad reach — and
**passes** (exit zero) on your least-privilege policy. Run it against both the original
`NotifierPolicy` and your fix and show it flips. Have a model draft the rule (a Checkov-style
static check, or a `simulate-principal-policy` assertion that the role is denied `iam:CreateUser` /
`s3:GetObject` on anything outside its named resources); review every line and confirm it fails the
original for the *right* reason — the role's reach, not an unrelated nit. This is your verdict made
un-recurrable, and the gate a real org would put in CI so no future function ships with `AdministratorAccess`
"to tighten later."

## AI acceleration
Paste the original execution-role policy into a model: "You're a red-team operator with code execution in
a Lambda using this role. List the highest-impact path to account compromise — each step, the IAM action,
the ATT&CK technique." It's reliable on the obvious composes (`iam:CreateUser` → attach admin; `s3:*` →
exfil). Validate each hop with `simulate-principal-policy` (it can't see SCPs/boundaries). Then paste your
guardrail and your least-privilege policy and ask it to author a role that sneaks past the check — if it
can, your rule is too narrow.

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
  LocalStack), fetch it at runtime, and show the env-var dump no longer leaks it.
