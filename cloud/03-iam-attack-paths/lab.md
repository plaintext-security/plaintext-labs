# Lab 03 — Predict the Path, Cut the Graph: IAM Privesc as Reachability

> **Hands-on lab.** Environment: `plaintext-labs/cloud/03-iam-attack-paths` (runs on **floci**, a free,
> MIT-licensed local AWS emulator — no cloud account, no real credentials). Objective: **model the
> account as a directed graph, find every path from a low-privilege principal to admin, then implement
> the minimum cut-set and re-run the graph to prove no path remains.** Target: **~90 min**, one finish
> line. [← Back to the module concept](README.md)

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The account is a directed graph.** | Principals are nodes; an edge A→B means "A holds a permission that lets it *become* B." Privesc is reachability to an `is_admin` node. |
| 2 | **An escalation primitive draws an edge; a reach-only permission does not.** | `iam:PassRole`, `iam:CreatePolicyVersion`, `iam:AttachUserPolicy`, `sts:AssumeRole` grant new power → edges. `s3:GetObject` is terminal → no edge. |
| 3 | **Multi-hop chains are invisible to flat policy review.** | No single principal has an obvious over-grant; the escalation lives in the *edges between* them. This is the entire reason `pmapper` exists. |
| 4 | **`dev-alice` reaches admin in two hops holding nothing alarming.** | `sts:AssumeRole` → `LambdaRole`, then `iam:PassRole` + `lambda:UpdateFunctionConfiguration` → run as `AdminRole`. |
| 5 | **A minimum cut-set, not a cut.** | Severing one edge breaks one path; if a second path survives, the account is still compromised. Cut the smallest edge set that disconnects *all* paths. |
| 6 | **"Fixed" means no path, proven — not a recommendation.** | Implement the cut, re-run the analyzer, and confirm **"No paths to admin found"** + exit 0. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [graph, revealed](README.md#the-graph-revealed).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Of `iam:CreatePolicyVersion`, `s3:GetObject`, `iam:PassRole`, `cloudwatch:GetMetricData` — which two
   draw edges in the graph, and what single question separates an escalation primitive from an inert one?
2. `dev-alice` has no admin grant, no `iam:*`, and can only `sts:AssumeRole` one Lambda role. Why is she
   *not* safe — and where does the escalation actually live?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/03-iam-attack-paths
make up                              # build + seed the floci escalation scenario
make demo                            # worked path-finder walkthrough over the bundled graph
make shell                           # drop into the container (pmapper + cloudfox + aws) to work
make analyze GRAPH=data/graph.json   # run the path finder against any graph file
make down                            # stop when done
```

**What this lab is — and isn't (read this).** **A local emulator does not *enforce* IAM** — a denied
`AssumeRole` won't actually bounce, so you can't prove a chain by detonating it against the API. That's
fine: privesc here is a **graph property, evaluated logically.** A pre-built `data/graph.json` (the
pmapper-style graph for this account) ships with the lab so the reachability analysis is deterministic;
you corroborate its edges against the live seeded policies with `aws`/`cloudfox`, and — where you want
AWS's own policy logic on a single edge — with `aws iam simulate-principal-policy` (which returns
`allowed`/`denied` + why against the *real* evaluation engine). So "she reaches admin" and later "the path
is gone" are both **graph evaluations over policies you can read**, not lucky API calls. Because the lab
drives plain `aws`/`cloudfox` via `AWS_ENDPOINT_URL`, the identical steps later run against a **real AWS
account you own** to watch enforcement live. Mark any hop you can't detonate as *assessed from config.*

> **▸ On track if:** `make demo` lists `dev-alice` under Users and `LambdaRole` / `AdminRole` under Roles,
> then reports **`FOUND 1 path(s) to admin`** for `graph.json` (exit non-zero) and **`No paths to admin
> found. Graph is clean.`** for the shipped `graph-fixed.json` (exit 0) — the scenario is live.

> **Authorization note.** IAM attack-path analysis is offensive by nature — it enumerates how to become
> admin. **Only run it against accounts you own or have explicit written permission to test.** Everything
> here runs locally against a simulated account you own. For a *real*-enforcement rerun, use an
> intentionally vulnerable target you provision yourself — **CloudGoat** `iam_privesc_by_*` in your own
> free-tier account (the stretch), never a shared, production, or third-party account. Never point
> `pmapper`/`cloudfox` at an account you do not own.

---

## Scenario

The target account's CISO wants a privilege-escalation map ahead of the annual review. You hold
read-only credentials equivalent to `dev-alice` — a developer with no admin grant, no `iam:*`, and no
ability to attach a policy to herself. Your deliverable is a **blast-radius finding plus the proven
fix**: every path from `dev-alice` to admin, the minimum cut-set that breaks *all* of them, and a graph
re-run proving the path is gone. Each step runs the same rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Step 1 — Map the principals, then predict the reach

**Concept (30 sec):** Flight-card #1 & #3. You are about to look for something flat policy review can't
see — an *edge between* principals — so start by cataloguing the nodes and committing a gut call.

**Predict, then do:** write your verdict (is `dev-alice` safe?), then enumerate:
`aws iam list-users`, `aws iam list-roles`, and read her attached policy
(`aws iam list-attached-user-policies --user-name dev-alice`, then `get-policy-version`).

> **▸ On track if:** her *only* notable permission is a single `sts:AssumeRole` on one role, and every
> policy you read looks individually harmless. **Record:** "no obvious over-grant" — the trap this module
> exists to spring.

### Step 2 — Build the graph and reveal the reach (the heart of it)

**Concept (30 sec):** Flight-card #4. Once the account is a graph, "find all privesc paths" is a
reachability search — milliseconds, not an afternoon of squinting at JSON.

**Do it:** run the finder over the bundled graph:
```bash
make analyze GRAPH=data/graph.json
```

> **▸ On track if:** the analyzer prints **`FOUND 1 path(s) to admin`**, shows `dev-alice --> [2 hop(s)]
> --> AdminRole (ADMIN)`, and **exits non-zero** — *paths to admin exist.* **Record:** how many distinct
> paths the finder reports, and that a **discovered privesc edge** now exists where flat review saw none.

### Step 3 — Walk the two-hop chain and name each primitive

**Concept (30 sec):** Flight-card #2. Each hop is one Rhino "21 methods" primitive — an edge, not a bug.

**Do it:** read the path the analyzer printed, and confirm hop 1's trust relationship live:
```bash
aws iam get-role --role-name LambdaRole --query "Role.AssumeRolePolicyDocument"
```
- **Hop 1** — `dev-alice → LambdaRole` via `sts:AssumeRole` (she's an explicit principal in the role's
  trust policy). ATT&CK **T1078.004** (Valid Accounts: Cloud).
- **Hop 2** — `LambdaRole → AdminRole` via `iam:PassRole` + `lambda:UpdateFunctionConfiguration`: re-point
  an existing Lambda's execution role to the admin role, invoke it, and the code runs as admin. ATT&CK
  **T1548** (Abuse Elevation Control Mechanism).

> **▸ On track if:** the trust policy names `dev-alice` (confirming hop 1's edge), and you can say in one
> sentence that *no single principal here holds an obvious over-grant* — the escalation is the two edges.
> **Record:** the Rhino primitive + ATT&CK ID per hop.

### Step 4 — Corroborate every edge against the live policies

**Concept (30 sec):** Flight-card #6 in reverse — the graph is only trustworthy if it matches reality; no
hop may rest on the model alone.

**Do it:** confirm `LambdaRole` really holds the hop-2 primitives, and — for AWS's own verdict on the
edge — ask the policy evaluator directly:
```bash
cloudfox aws --profile local permissions | grep -i LambdaRole   # or: aws iam get-role-policy / list-attached-role-policies
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::000000000000:role/LambdaRole \
  --action-names iam:PassRole lambda:UpdateFunctionConfiguration \
  --resource-arns arn:aws:iam::000000000000:role/AdminRole \
  --query 'EvaluationResults[*].[EvalActionName,EvalDecision]' --output table
```

> **▸ On track if:** `cloudfox` shows `LambdaRole` holding `iam:PassRole` *and*
> `lambda:UpdateFunctionConfiguration` (the **enumerated over-broad grant** behind hop 2), and
> `simulate-principal-policy` returns **`allowed`** for those actions — AWS's evaluator agreeing the edge
> is real. **Record:** edge ↔ live policy, so no hop is asserted on the model alone. *(On floci, treat a
> `simulate` result as the policy-logic verdict; the same call proves enforcement on real AWS.)*

---

## Prove the control (your finish line)

Naming the cut is the finding; **implementing it and proving the path is gone is the fix.** In a graph,
"fixed" means *no path*, not *a recommendation*. Do all three, then check the honesty bar:

1. **Identify the minimum cut-set.** Which single edge, removed, disconnects *every* path from `dev-alice`
   to admin? Predict, then check against the graph's `minimum_cut_set` metadata (printed by the analyzer).
   The cheapest cut here is scoping `iam:PassRole` on `LambdaRole` from `Resource: "*"` to the one role it
   legitimately passes — so it can no longer pass `AdminRole`, severing hop 2. (The alternative — removing
   `dev-alice` from the trust policy — severs hop 1; note why scoping the resource is cheaper
   operationally.) **Write the exact corrected policy statement.**
2. **Implement the cut as a graph operation, then re-run.** Copy `data/graph.json` to
   `data/graph-fixed.json` and remove the one edge your cut-set targets (the `LambdaRole → AdminRole`
   `PassRole+UpdateFunction` edge — the graph effect of scoping the `iam:PassRole` resource). **Don't
   over-cut**: remove only the edge the minimal policy change removes. Then:
   ```bash
   make analyze GRAPH=data/graph-fixed.json   # or: make verify-cut
   ```
3. **The finish line:** the re-run prints **`No paths to admin found. Graph is clean.`** and **exits 0.**
   If a path still shows, your cut hit the wrong edge — a second path survived, which is the whole reason
   "cut-*set*" is the right word.

> **▸ On track if:** you hold a **mapped, proven privesc path** (two hops, each with live-policy evidence
> and an ATT&CK ID) *and* a `graph-fixed.json` the analyzer certifies clean at exit 0 — the before
> (`FOUND 1 path`, non-zero) vs. after (clean, zero) is your proof the fix holds.

Score your three README "Call it" predictions against the reveals; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. What single question separates an escalation primitive from an inert permission, and which of the four
   README permissions draw edges?
2. `dev-alice` holds nothing alarming yet reaches admin in two hops — name each hop's primitive and ATT&CK
   technique, and say where the escalation actually lives.
3. Why is scoping the `iam:PassRole` *resource* (not deleting the role) the minimal change, and what makes
   "cut-set" — not "cut" — the correct word?

---

## Deliverables

- **`remediation.md`** — the CISO finding: each path numbered, the edges that compose it (with live-policy
  evidence and ATT&CK ID), the severity, and the corrected policy statement that breaks it.
- **`graph-fixed.json`** — the graph with your cut applied, which the analyzer confirms is clean (exit 0).

Commit both. *Do not commit credentials, real account data, or emulator volumes.*

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your verdict is "no principal should be able to
reach an admin node." Encode it as a **guardrail that fails the bad state and passes the fix.**
`analyze.py` already exits non-zero when any path to admin exists and accepts `--json-report`; turn that
into a posture gate: a small wrapper (or CI step) that runs the analyzer over a graph, **fails the build
on the original `graph.json`** and **passes on `graph-fixed.json`**, emitting the JSON report (`source`,
`destination`, `hops`, `remediation_action`) as the evidence artifact. Have a model draft the wrapper and
report schema; **review every line** and confirm it fails the original for the *right* reason (a real path
to admin, not a parse error). This is the IAM posture check the Phase-1 project gates CI on — your verdict
made un-recurrable.

## Definition of done (`iam-attack-paths` ✅)

- [ ] `make analyze GRAPH=data/graph.json` reports a path from `dev-alice` to admin and exits non-zero.
- [ ] You enumerated every path and named the Rhino primitive + ATT&CK technique (T1078.004, T1548) at each hop.
- [ ] You corroborated each edge against the live seeded policy with `cloudfox`/`aws` (and, on one edge, `simulate-principal-policy` returned `allowed`) — no hop rests on the model alone.
- [ ] You wrote the minimal corrected policy statement and can say why scoping the `iam:PassRole` *resource* is the minimal change.
- [ ] `data/graph-fixed.json` makes the analyzer report **no paths to admin** and **exit 0** — you *implemented* the cut and re-ran, not just proposed it.
- [ ] The `Automate & own it` guardrail fails `graph.json` and passes `graph-fixed.json`.
- [ ] You scored your three "Call it" predictions and can explain all six flight-card facts cold.

## Connects forward

The principal you cut to size in **module 02 (Cloud Identity & IAM)** is now one node in a graph. Module
**14 (Cloud Attack Techniques)** *detonates* one of these privesc paths with stratus-red-team/Pacu to
generate the telemetry module **15 (Cloud Logging & Detection)** detects. The same posture-gate pattern
returns in the **Phase-1 capstone**, which closes every breach hop as code gated by exactly this kind of
check in CI — the over-broad role that opened the [Capital One chain in module 01](../01-cloud-fundamentals/README.md)
is this same edge, cut before an SSRF ever reaches it.

## Marketable proof

> "I model an AWS account as a directed graph, find every multi-hop privilege-escalation path to admin
> with pmapper/cloudfox, and produce a minimum-cut-set remediation — then I *implement* the cut and re-run
> the graph to prove no path to admin remains, and ship the analyzer as a CI posture gate that fails the
> build on any reachable admin node."

## Stretch

- Re-run the whole loop against a CloudGoat `iam_privesc_by_rollback` (or `iam_privesc_by_key_rotation`)
  scenario in a real free-tier account **you own**, where IAM is actually enforced — detonate the path,
  apply your cut, and confirm the privesc call now genuinely *fails*, not just disappears from the graph.
- Add a second path to admin: edit `data/graph.json` to introduce a third-hop path through a new role,
  re-run the analyzer to confirm it's found, and show your *original* single-edge cut no longer
  disconnects the graph — you now need a larger cut-set. Proof the analyzer graph-searches, not
  pattern-matches one known path.
- Write a graph builder (`build_graph.py`) that generates `graph.json` by calling `aws`/`cloudfox` instead
  of using the bundled file — the first step toward a self-updating IAM posture monitor.
