# Lab 03 — Predict the Path, Cut the Graph: IAM Privesc as Reachability

*Variant D · breach-driven, predict-the-blast-radius (graph). [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It seeds a
[LocalStack](https://localstack.cloud/) account with a multi-hop escalation scenario
and analyses it with a bundled graph analyzer (`analyze.py`) alongside `pmapper`/`cloudfox` — no cloud
account or real credentials.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/03-iam-attack-paths
make up                          # build + seed the LocalStack escalation scenario
make demo                        # worked path-finding walkthrough over the bundled graph
make shell                       # drop into the container (pmapper + cloudfox + awslocal) to work
make analyze GRAPH=data/graph.json   # run the path finder against any graph file
make down                        # stop when done
```

**What this lab is — and isn't (read this).** **LocalStack CE does not *enforce* IAM** — a denied
`AssumeRole` won't actually bounce, so you can't prove a chain by detonating it against the API. That's
fine: privesc here is a **graph property, evaluated logically.** A pre-built `data/graph.json` (the
pmapper-style graph for this account) ships with the lab so the reachability analysis is deterministic;
you corroborate its edges against the live seeded policies with `awslocal`/`cloudfox`. So "she reaches
admin" and later "the path is gone" are both **graph evaluations** over policies you can read, not lucky
API calls. Honest tool, honest answer — mark any hop you can't detonate as *assessed from config*.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against a simulated account you own. Never run attack-path analysis against accounts you do not own.

## Scenario
The target account's CISO wants a privilege-escalation map ahead of the annual review. You hold
read-only credentials equivalent to `dev-alice` — a developer with no admin grant, no `iam:*`, and no
ability to attach a policy to herself. Your deliverable is a **blast-radius finding plus the proven
fix**: every path from `dev-alice` to admin, the minimum cut-set that breaks *all* of them, and a graph
re-run proving the path is gone.

Each step runs the same rhythm: **Predict** (commit before you look) → **Do** (build/query the graph) →
**Reveal** (check your call) → **Record** (one line for the CISO finding).

## Do

### Part 1 — Predict the reach, then build the graph

1. [ ] **Map the principals.** List users and roles (`awslocal iam list-users`,
   `awslocal iam list-roles`) and read `dev-alice`'s attached policy. **Predict** before going further:
   she has no obvious over-grant — is she safe? **Record:** her *only* notable permission is
   `sts:AssumeRole` on one role.

2. [ ] **Build / load the graph.** Run `make demo` (or `make analyze GRAPH=data/graph.json`). The
   analyzer loads the pmapper-style graph, finds every path from a non-admin node to an `is_admin` node,
   and prints each hop with the API calls that compose it. **Reveal:** `dev-alice` reaches
   `AdminRole` in **two hops** — and the demo exits non-zero, because *paths to admin exist.*
   **Record:** how many distinct paths the finder reports.

3. [ ] **Walk the chain end-to-end.** Read the path the analyzer printed:
   - **Hop 1** — `dev-alice → LambdaRole` via `sts:AssumeRole` (she's an explicit principal in
     the role's trust policy). **Predict then confirm** with
     `awslocal iam get-role --role-name LambdaRole --query "Role.AssumeRolePolicyDocument"`.
   - **Hop 2** — `LambdaRole → AdminRole` via `iam:PassRole` +
     `lambda:UpdateFunctionConfiguration`: update an existing Lambda's execution role to the admin role,
     invoke it, and the code runs as admin. **Record** which Rhino "21 methods" primitive each hop is.

4. [ ] **Corroborate the edges against the live policies.** The graph is only trustworthy if it matches
   reality. Use `cloudfox aws --profile localstack permissions` (or `awslocal iam get-role-policy` /
   `list-attached-role-policies`) to confirm `LambdaRole` really holds `iam:PassRole` and
   `lambda:UpdateFunctionConfiguration`. **Record:** edge ↔ policy, so no hop is asserted on the model
   alone. Map each hop to its ATT&CK technique (T1078.004 for hop 1, T1548 for hop 2).

### Part 2 — Find the cut-set, implement it, and re-run the graph

Naming the cut is the finding; **implementing it and proving the path is gone is the fix** — in a graph,
"fixed" means *no path*, not *a recommendation*.

5. [ ] **Identify the minimum cut-set.** Which single edge, removed, disconnects *every* path from
   `dev-alice` to admin? **Predict, then check** against the graph's `minimum_cut_set` metadata. The
   cheapest cut here is scoping `iam:PassRole` on `LambdaRole` from `Resource: "*"` to the one
   role it legitimately passes — so it can no longer pass `AdminRole`, severing hop 2. (The
   alternative cut — removing `dev-alice` from the trust policy — severs hop 1; note why one is cheaper
   operationally.) **Record** the exact corrected policy statement.

6. [ ] **Implement the cut as a graph operation.** Copy `data/graph.json` to `data/graph-fixed.json` and
   remove the one edge your cut-set targets (the `LambdaRole → AdminRole`
   `PassRole+UpdateFunction` edge — that is the *graph effect* of scoping the `iam:PassRole` resource).
   This is the verdict from step 5 applied to the model. **Don't over-cut** — remove only the edge the
   minimal policy change removes; if you delete more, you've cut more than least privilege allows.

7. [ ] **Re-run the graph and prove the path is gone.** Run
   `make analyze GRAPH=data/graph-fixed.json`. It must print **"No paths to admin found. Graph is
   clean."** and **exit 0.** If a path still shows, your cut hit the wrong edge — a second path survived,
   which is the entire reason "cut-*set*" is the right word. **Record:** the before (non-zero, 1 path)
   vs. after (zero, clean) as the proof the fix holds.

8. [ ] **(In-lab stretch) Add a second path, then re-cut.** Edit `data/graph.json` to add a third-hop
   path to admin through a new role, re-run the analyzer to confirm it's found, and show that your
   *original* single-edge cut no longer disconnects the graph — you now need a larger cut-set. This
   proves the analyzer is genuinely graph-searching, not pattern-matching one known path.

## Success criteria — you're done when
- [ ] You enumerated every path from `dev-alice` to admin and named the escalation primitive (a Rhino
  "21 methods" entry) and ATT&CK technique at each hop.
- [ ] You corroborated each graph edge against the live seeded policy with `cloudfox`/`awslocal` — no hop
  rests on the model alone.
- [ ] You identified a **minimum cut-set**, wrote the corrected policy statement, and can say in one
  sentence why scoping the `iam:PassRole` *resource* (not deleting the role) is the minimal change.
- [ ] Your `data/graph-fixed.json` makes the analyzer report **no paths to admin** and **exit 0** — you
  *implemented* the cut and re-ran the graph, not just proposed it.
- [ ] You scored your three "Call it" predictions from the README against the reveals.

## Deliverables
`remediation.md` — the CISO finding: each path numbered, the edges that compose it (with the live-policy
evidence and ATT&CK ID), the severity, and the corrected policy statement that breaks it.
`graph-fixed.json` — the graph with your cut applied, which the analyzer confirms is clean. Commit both.
Do not commit credentials, real account data, or LocalStack volumes.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your verdict is "no principal should be able
to reach an admin node." Encode it as a **guardrail that fails the bad state and passes the fix.**
`analyze.py` already exits non-zero when any path to admin exists and accepts `--json-report`; turn that
into a posture gate: a small wrapper (or a CI step) that runs the analyzer over a graph, **fails the
build (exit non-zero) on the original `graph.json`** and **passes on `graph-fixed.json`**, emitting the
JSON report (`source`, `destination`, `hops`, `remediation_action`) as the evidence artifact. Have a
model draft the wrapper and report schema; review every line and confirm it fails the original for the
*right* reason (a real path to admin, not a parse error). This is the IAM posture check the Phase-1
project gates CI on — your verdict made un-recurrable.

## AI acceleration
Paste `graph.json` (or the raw policies) into a model and ask it to enumerate every path to admin and
draft the CISO summary. It's reliable on single-hop edges and excellent at business-language wording —
but it misses multi-hop chains through intermediate roles roughly half the time and invents edges from
services it doesn't model. Never use it as the source of truth for path enumeration; use `analyze.py`/
`pmapper` for that. Then paste your cut and ask it to find a path that survives — if it can, your
cut-set is incomplete.

## Connects forward
The principal you cut to size in module 02 is now one node in a graph; module **14 (Cloud Attack
Techniques)** *detonates* one of these privesc paths with stratus-red-team/Pacu to generate the
telemetry that module 15 detects. The same posture-gate pattern returns in the **Phase-1 capstone**,
which closes every breach hop as code gated by exactly this kind of check in CI.

## Marketable proof
> "I model an AWS account as a directed graph, find every multi-hop privilege-escalation path to admin
> with pmapper/cloudfox, and produce a minimum-cut-set remediation — then I *implement* the cut and
> re-run the graph to prove no path to admin remains, and ship the analyzer as a CI posture gate that
> fails the build on any reachable admin node."

## Stretch
- Re-run the whole loop against a CloudGoat `iam_privesc_by_rollback` (or `iam_privesc_by_key_rotation`)
  scenario in a real free-tier account, where IAM is actually enforced — detonate the path, then apply
  your cut and confirm the privesc call now genuinely fails, not just disappears from the graph.
- Write a graph builder (`build_graph.py`) that generates `graph.json` by calling `awslocal`/`cloudfox`
  instead of using the bundled file — the first step toward a self-updating IAM posture monitor.
