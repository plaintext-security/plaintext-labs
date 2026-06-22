# Lab 03 — IAM Attack Path Analysis with pmapper

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo.
The environment seeds a LocalStack account with a Meridian Financial multi-hop privilege-escalation
scenario, then uses `pmapper` and a bundled Python analysis script against it. A pre-built `graph.json`
(the output `pmapper graph create` would produce against the live account) is included so you can
analyse the attack path structure even if pmapper's LocalStack integration needs adjustment.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/03-iam-attack-paths
make up        # build + seed the LocalStack escalation scenario
make demo      # run the worked path-finding walkthrough
make shell     # drop into the container to work interactively
make down      # stop when done
```

The seeded scenario: `dev-alice` → assume `MeridianLambdaRole` (via `sts:AssumeRole`) → invoke a
Lambda that has `MeridianAdminRole` as its execution role → role has `iam:*` and `s3:*`. Three hops
from unprivileged user to full admin. The `data/graph.json` represents the pmapper graph for this
account so you can load and query it even offline.

> Only test accounts you own or have explicit written permission to test. This lab uses a simulated
> environment — never run attack-path analysis against real accounts you do not own.

## Scenario
Meridian Financial's CISO has asked you to produce a privilege-escalation map for their AWS account
ahead of their annual security review. You have read-only credentials equivalent to `dev-alice`'s
permissions. Your deliverable: every path from `dev-alice` to admin privileges, the cheapest
remediation that breaks all paths, and a one-page summary for the CISO.

## Do
1. [ ] **Explore the bundled graph.** Open `data/graph.json` and identify the nodes (principals) and
   edges (permission-composition relationships). Which principal is the escalation destination (the
   node with `AdministratorAccess`)? Hint: look for `"is_admin": true` in the node data.

2. [ ] **Run the bundled `analyze.py` script.** This script loads `data/graph.json` and prints all
   paths from `dev-alice` to any admin node, along with the API calls required at each hop.
   Hint: `python analyze.py data/graph.json`.  How many distinct paths to admin exist?

3. [ ] **Trace hop 1: dev-alice → MeridianLambdaRole.** What permission does dev-alice have that
   creates this edge? Check `dev-alice`'s policy. Is it a direct `sts:AssumeRole` or something
   that implies it?

4. [ ] **Trace hop 2: MeridianLambdaRole → MeridianAdminRole.** The Lambda execution role has
   `iam:PassRole` and `lambda:UpdateFunctionConfiguration`. What does an attacker do with these
   two permissions combined? (Hint: they can update the Lambda's execution role to MeridianAdminRole,
   then invoke the Lambda to act as admin.)

5. [ ] **Use cloudfox or awslocal to verify.** Confirm that the edges in the graph match the actual
   policies seeded in LocalStack. Hint:
   `awslocal iam get-role --role-name MeridianLambdaRole --query "Role.AssumeRolePolicyDocument"`.

6. [ ] **Identify the minimum cut-set.** Which single edge, if removed, breaks all paths from
   dev-alice to admin? Write your answer in `remediation.md` with the specific policy change (e.g.,
   scope `iam:PassRole` on `MeridianLambdaRole` to `Resource: arn:aws:iam::*:role/MeridianLambdaRole`
   only).

7. [ ] **Implement the cut and re-verify.** Don't just propose it — *apply* it and prove it. Copy
   `data/graph.json` to `data/graph-fixed.json` and remove the one edge your cut-set targets (the
   `MeridianLambdaRole → MeridianAdminRole` PassRole edge — that's the graph effect of scoping the
   `iam:PassRole` resource). Then run `make verify-cut` (`analyze.py data/graph-fixed.json`). It must
   print **"No paths to admin found. Graph is clean."** and exit 0. A reference `graph-fixed.json` is
   bundled — try it yourself first, then compare. If a path still shows, you cut the wrong edge.

8. [ ] **Run `make demo`** and compare: it now shows the path BEFORE the cut and the clean graph
   AFTER, end to end.

## Success criteria — you're done when
- [ ] You can enumerate all paths from `dev-alice` to admin and describe each hop.
- [ ] You've identified the specific permission at each edge.
- [ ] You've proposed a minimum cut-set and written the corrected policy statement.
- [ ] Your `data/graph-fixed.json` makes `analyze.py` report no paths and exit 0 — you *implemented*
  the cut and verified the path is gone, not just proposed it.

## Deliverables
`remediation.md` — structured finding: each escalation path (numbered), the edges that compose it,
the severity, and the corrected policy statement that breaks it. `graph-fixed.json` — the graph with
your cut applied, which `analyze.py` confirms is clean. Commit both. Do not commit real credentials
or real AWS data.

## Automate & own it
**Required.** Extend `analyze.py` to output a JSON report suitable for a CI gate — a list of
escalation paths, each with `source`, `destination`, `hops`, and `remediation_action`. The gate
should exit non-zero if any path to admin exists (so a CI job running it against a live account
would fail the build). Have a model draft the JSON output format and the exit-code logic; you review
every line and confirm the script exits non-zero against the current `graph.json` and exits zero
against a corrected version. This is the skeleton of an IAM posture gate.

## AI acceleration
Paste the `graph.json` into a model and ask it to enumerate all paths to admin nodes. It will get
the single-hop paths right reliably; it will miss multi-hop paths through intermediate roles roughly
50% of the time. Use the model to draft the CISO summary — it's well-suited to translating technical
findings into business language. But never use it as the source of truth for the path enumeration;
use `analyze.py` or pmapper for that.

## Connects forward
The attack paths identified here are the precise misconfigurations that module 05 (Posture &
Misconfiguration Auditing) would catch with a `prowler` check and module 06 (IaC Security) would
prevent at plan time with a Checkov rule.

## Marketable proof
> "I can build an IAM privilege-escalation graph, find multi-hop paths to admin, and produce a
> minimum-cut remediation plan — the deliverable expected from a cloud security assessment."

## Stretch
- Edit `data/graph.json` to add a fourth-hop path through a new role and confirm `analyze.py` finds
  it. This validates that your analysis tool is actually graph-searching, not pattern-matching.
- Write a pmapper-compatible graph builder (`build_graph.py`) that generates a `graph.json` by
  calling `awslocal` — the first step toward a self-updating IAM posture monitor.
