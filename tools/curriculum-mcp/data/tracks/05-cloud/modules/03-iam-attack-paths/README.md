# Module 03 — IAM Attack Paths

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *privilege escalation in the cloud isn't a vulnerability — it's a policy composition that an attacker walks like a graph.*

## Why this matters
In traditional network pentests, privilege escalation means exploiting a vulnerability. In the cloud,
the most dangerous escalation paths are entirely within the intended behaviour of IAM — the attacker
simply chains legitimate API calls that the policy permits. These paths are invisible to any single
policy review but obvious once you model the account as a graph. `pmapper` and `cloudfox` exist
because human eyeballing of flat policy lists reliably misses the composed paths that attackers
exploit. Finding and fixing them before an attacker does is the core skill this module builds.

## Objective
Build and traverse an IAM privilege-escalation graph for a seeded Meridian Financial account, identify
all paths from a low-privilege starting principal to admin, and write a remediation plan that breaks
each path with a minimal, targeted policy change.

## The core idea
Think of an IAM account as a directed graph: principals are nodes, and an edge from A to B exists
whenever A can perform an action that results in A gaining B's permissions — or B's permissions being
applied to A. The edges aren't explicit; they're *implied* by the policy documents and the AWS service
actions that compose permissions across principals. `iam:PassRole` + `ec2:RunInstances` implies an
edge from the user to the EC2 role. `iam:CreateAccessKey` on another user implies an edge to that
user. `sts:AssumeRole` where the trust policy permits it implies a direct edge to the role. The
escalation isn't a bug — it's the graph navigated intentionally.

What makes this tractable as a tool problem rather than an infinite enumeration is that the graph is
bounded: the number of principals and the set of actions that imply edges are finite and known. pmapper
treats each known escalation technique as a typed edge, builds the full graph in memory, and runs
reachability queries against it. The question "can any principal reach admin?" becomes a graph search
for all nodes from which admin is reachable — which takes milliseconds for accounts with hundreds of
roles, where a human reading policy documents would take hours and still miss multi-hop paths.

The multi-hop path is what makes this particularly dangerous in practice. A single user might have
no obvious over-broad permission; every individual policy might look reasonable in isolation. But user
A can assume role B, and role B can pass role C to a Lambda, and role C has `iam:*`. No single step
looks alarming; the chain is admin escalation. The graph makes the chain visible. This is why the
standard cloud security assessment discipline is: enumerate the graph, find all paths to admin, fix
the *edge* in the path that is cheapest to remove (usually the one that can be removed with the least
operational disruption), then re-run the graph to confirm the path is severed.

Remediating IAM attack paths requires the same discipline as remediation of any graph vulnerability:
breaking one edge isn't enough if there are multiple paths to the same destination. The minimum
effective remediation is a cut-set — a set of edges whose removal disconnects all paths from the
starting node to admin. In practice, the cheapest cut-sets are almost always: (1) scope `iam:PassRole`
to the specific roles the principal legitimately needs to pass rather than `*`, or (2) add a condition
key (like `iam:PassedToService`) that restricts PassRole to a specific service, or (3) remove
unnecessary `sts:AssumeRole` from trust policies where a more specific principal would serve the
same legitimate purpose. The graph shows you what to cut; the CONTRIBUTING.md principle of "minimal,
targeted change" tells you not to cut more than you need to.

## Learn (~4 hrs)

**IAM privilege escalation theory (~1.5 hrs)**
- [Rhino Security Labs — AWS IAM Privilege Escalation Methods and Mitigation](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/) — the definitive reference for 21 known IAM escalation paths, each with the required permissions and mitigation. Essential reading before the lab.
- [MITRE ATT&CK T1548 — Abuse Elevation Control Mechanism: Cloud](https://attack.mitre.org/techniques/T1548/) and [T1078.004 — Valid Accounts: Cloud Accounts](https://attack.mitre.org/techniques/T1078/004/) — the ATT&CK techniques that IAM privilege escalation maps to.

**pmapper (~1.5 hrs)**
- [pmapper GitHub — README](https://github.com/nccgroup/PMapper) — the graph-based IAM analysis tool from NCC Group. Read the "how it works" and "usage" sections; focus on `pmapper graph create`, `pmapper analysis`, and `pmapper visualize`.
- [NCC Group Research — Mapping AWS IAM Privilege Escalation Paths with PMapper](https://research.nccgroup.com/2018/12/12/aws-iam-escalation-paths/) — the original analysis that motivated pmapper; it explains the graph model and why flat policy review misses multi-hop paths.

**cloudfox attack-path commands (~1 hr)**
- [cloudfox GitHub — `privesc` and `iam-simulator`](https://github.com/BishopFox/cloudfox) — cloudfox's privilege escalation detection commands; the `privesc` module automates path finding similar to pmapper. Read the "AWS" section of the docs.

## Key concepts
- IAM as a directed graph: principals as nodes, permission-composition as edges
- The 21 known escalation techniques (PassRole, CreateAccessKey, AssumeRole, Lambda invocation, etc.)
- Why multi-hop paths are missed by flat policy review
- Graph reachability as a query: "who can reach admin?"
- Minimum cut-sets: scoping PassRole, conditioning AssumeRole, removing unnecessary federation trust
- ATT&CK mapping: T1548 (elevation) and T1078.004 (valid accounts)

## AI acceleration
Give a model the list of principals, their permissions, and role trust policies and ask it to trace
escalation paths manually. It is useful for single-hop paths; it reliably misses three-hop chains and
tends to hallucinate edges from services it doesn't fully model (Lambda execution, ECS task roles).
Use the model for the first-pass description and remediation wording — then validate every reported
path by checking it against the pmapper graph or the cloudfox privesc output before you include it
in a report. Graph tools are faster and more reliable than model enumeration for this task.
