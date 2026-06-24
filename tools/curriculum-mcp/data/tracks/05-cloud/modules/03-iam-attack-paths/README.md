# Module 03 — IAM Attack Paths

*Variant D · breach-driven, predict-the-blast-radius (graph). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *privilege escalation in the cloud isn't a vulnerability; it's a path through a graph that legitimate permissions drew for you.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 02 — Cloud Identity & IAM](../02-cloud-identity-iam/README.md)
{ .module-meta }


## The research

In 2018, **Rhino Security Labs** published a catalogue that should be uncomfortable reading for anyone
who signs off on IAM policies: **["AWS IAM Privilege Escalation — 21 Methods"](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/)**.
Not 21 bugs in AWS — 21 *combinations of permissions that AWS grants exactly as intended* and that
nonetheless let a low-privilege principal become administrator. `iam:CreatePolicyVersion` lets you
write a new version of a policy you're attached to — so set it to `Allow *:*`. `iam:PassRole` plus a
launch action (`ec2:RunInstances`, `lambda:CreateFunction`) lets you hand an admin role to a compute
resource you control and *become* it. `iam:AttachUserPolicy` lets you attach `AdministratorAccess` to
yourself. Each is one line in a policy. None is a CVE. Every one is admin.

The catalogue's real lesson isn't the list — it's that these paths are **invisible to policy review.**
A human reading flat policy documents one at a time cannot see that user A can assume role B, which can
pass role C to a Lambda, which has `iam:*`. No single step looks alarming; the *composition* is total
compromise. So this module turns on a prediction, and the naive guess is reliably wrong:

> **Given a menu of ordinary-looking permissions, which ones chain to admin — and how many hops away
> is "admin" from a principal that has none of the obvious red-flag grants?**

## Your job

By the end of this module you'll **model an entire account as a directed graph and predict its blast
radius**: principals are nodes, and an edge from A to B means *A holds a permission that lets it become
B*. You'll build the graph with **`pmapper`/`cloudfox`**, walk a real multi-hop chain from a
low-privilege user to admin, find the **minimum cut-set** — the smallest set of edges whose removal
disconnects *every* path to admin — then **implement the cut and re-run the graph to prove the edge is
gone.** That last beat is what separates an assessment from a report: in IAM, "fixed" means the path no
longer exists in the graph, not that someone wrote a recommendation.

## Call it before you read on

Don't scroll. Write down your gut answers — being wrong here is the teaching event, and you'll grade
yourself in the lab.

> **Q1.** Of these four permissions, which chain to admin: `iam:CreatePolicyVersion`, `s3:GetObject`,
> `iam:PassRole`, `cloudwatch:GetMetricData`? (Two are escalation primitives; two are inert.)
>
> **Q2.** `dev-alice` has *no* admin grant, *no* `iam:*`, and can't attach a policy to herself. She can
> only `sts:AssumeRole` one Lambda role. Is she safe — and if not, how many hops to admin?
>
> **Q3.** Two separate paths run from `dev-alice` to admin. You scope `iam:PassRole` on the role in
> path 1. Is the account fixed?

## The graph, revealed

Hold your answers against these.

**Q1 — escalation is a permission *type*, not a permission *name*.** `iam:CreatePolicyVersion` and
`iam:PassRole` are escalation primitives because they let a principal *change what it (or a resource it
controls) is allowed to do* — they create edges in the graph. `iam:CreatePolicyVersion` lets you author
`Allow *:*` into a policy you're already attached to; `iam:PassRole` lets you donate a more-powerful
role to compute you launch. `s3:GetObject` and `cloudwatch:GetMetricData` read data — they're reach, but
they're *terminal*: they grant no new permissions, so they draw no edges. The skill Rhino's catalogue
trains is reading a permission and asking **"does this let the holder grant itself or a resource more
power?"** If yes, it's an edge. The 21 methods are 21 answers to that one question.

**Q2 — she is two hops from admin, and nothing she holds looks dangerous.** `dev-alice` can assume
`LambdaRole` (hop 1, a plain `sts:AssumeRole` the trust policy permits). That role holds
`iam:PassRole` and `lambda:UpdateFunctionConfiguration` — so she updates an existing Lambda's execution
role to `AdminRole` and invokes it (hop 2). Now her code runs with `iam:*` and `s3:*`. **No
single principal in that chain has an obvious over-grant**; the escalation lives in the *edges between*
them, which is exactly why flat policy review misses it and why `pmapper` exists. The mental model to
keep: **the account is a directed graph, an edge is a permission that lets one principal become another,
and privilege escalation is just reachability to an admin node.** Once you see it that way, "find all
privesc paths" becomes "graph search from every principal to every `is_admin` node" — milliseconds, not
an afternoon of squinting at JSON.

**Q3 — no, and this is the whole reason "cut-set" is the right word.** Breaking one edge severs one
path; if a second path reaches admin through different edges, the account is still compromised. The
**minimum cut-set** is the smallest set of edges whose removal disconnects *all* paths from the source
to every admin node — a classic graph operation, and the actual deliverable of an IAM assessment. The
graph tells you *which* edge is cheapest to cut (usually scoping an `iam:PassRole` `Resource` from `*`
to the one role legitimately needed, or adding an `iam:PassedToService` condition, or removing an
over-broad principal from a trust policy); the discipline of the **minimal, targeted change** tells you
not to cut more than disconnects the graph. And — the beat that makes the verdict yours — you don't stop
at naming the cut. You apply it and **re-run the analysis**: a fixed account is one where the path finder
reports *no paths to admin*, proven, not promised.

## Learn (~4 hrs)

*Richer than a foundations module: the graph model here is the backbone of the Phase-1 project and the
capstone, so the time is well spent. Read Rhino's catalogue first — it's the source the tools encode.*

**The escalation catalogue (~1.5 hrs)**
- [Rhino Security Labs — AWS IAM Privilege Escalation — 21 Methods](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/) (~1 hr) — the primary research this whole module rests on. Read the PassRole, CreatePolicyVersion, AttachUserPolicy, and AssumeRole sections closely (those are the edges in the lab graph); skim the rest as a reference for *what a privesc edge looks like.*
- [MITRE ATT&CK T1548 — Abuse Elevation Control Mechanism: Cloud](https://attack.mitre.org/techniques/T1548/) and [T1078.004 — Valid Accounts: Cloud Accounts](https://attack.mitre.org/techniques/T1078/004/) (~30 min) — the technique IDs your finding cites; map each lab hop to one.

**The graph model and the tools (~1.5 hrs)**
- [tecRacer — Map out your IAM with PMapper](https://www.tecracer.com/blog/2021/08/map-out-your-iam-with-pmapper.html) (~30 min) — a walkthrough of *why* modeling IAM as a directed graph is the right abstraction: it works a concrete multi-hop chain (a developer edits a Lambda, borrows its existing role, mints an admin policy) that flat, policy-by-policy review would never surface.
- [pmapper — README (NCC Group)](https://github.com/nccgroup/PMapper) (~40 min) — read "how it works," then `pmapper graph create`, `pmapper analysis`, and `pmapper query`. This is the tool that turns the model above into a query.
- [BishopFox — cloudfox README (`permissions`, `role-trusts`)](https://github.com/BishopFox/cloudfox) (~20 min) — the enumeration accelerator you'll use to corroborate the graph against the live policies.

**The scenario range (~1 hr)**
- [CloudGoat — README and the `iam_privesc_by_*` scenarios (Rhino Security Labs)](https://github.com/RhinoSecurityLabs/cloudgoat) (~1 hr) — the same author's attack range; read one `iam_privesc_by_rollback` or `iam_privesc_by_key_rotation` scenario writeup so you've seen a privesc path run end-to-end in a *real* account, where IAM is actually enforced. The stretch re-runs the lab there.

## Key concepts
- The account is a **directed graph**: principals are nodes, an edge means "A can become B," privesc is reachability to an `is_admin` node
- An **escalation primitive** is any permission that lets the holder grant itself/a resource more power (`iam:PassRole`, `iam:CreatePolicyVersion`, `iam:AttachUserPolicy`, `sts:AssumeRole`); reach-only permissions draw no edges
- **Multi-hop paths** are invisible to flat policy review and obvious to graph search — this is why `pmapper`/`cloudfox` exist
- A **minimum cut-set** is the smallest set of edges whose removal disconnects *all* paths to admin; one cut edge is not a fix if a second path survives
- A fix is **proven** only when the re-run graph reports *no paths to admin* — implement the cut, don't just recommend it
- ATT&CK mapping: T1548 (elevation) and T1078.004 (valid accounts)

## AI acceleration
Give a model the principals, their policies, and the role trust policies and ask it to enumerate every
path to admin. It's a fast first-pass on single-hop edges and a strong drafter of the CISO summary — but
it has a known failure mode this module exists to expose: it reliably misses three-hop chains and
hallucinates edges from services it doesn't fully model (Lambda execution, ECS task roles). Treat its
path list as a *hypothesis*, never the source of truth: validate every reported path against the
`pmapper`/`cloudfox` graph, and confirm every *absence* of a path the same way. The judgment the model
can't do for you is the minimum cut — the smallest edge removal that disconnects all paths without
breaking the principal's real job — and the re-run that proves it. You direct it; you own the graph.
