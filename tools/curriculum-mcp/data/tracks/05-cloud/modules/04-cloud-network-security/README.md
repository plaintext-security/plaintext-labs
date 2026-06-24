# Module 04 — Cloud Network Security

*Variant D · breach-driven, predict-the-reachability, audit→build→re-verify ("find the exposure, author the baseline, prove it holds"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *a Security Group is the host firewall you already know, applied per-interface and composable — and your attack surface is the union of every rule, not any one of them.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 01 — Shared Responsibility](../01-cloud-fundamentals/README.md) · [Module 02 — Identity & IAM](../02-cloud-identity-iam/README.md)
{ .module-meta }


## The case

Between roughly **2017 and 2019** the same finding kept landing in the news under different company
names: a database or admin panel sitting on the open internet with **`0.0.0.0/0`** as its source range.
Internet-wide scanners (Shodan, BinaryEdge) catalogued **tens of thousands of exposed Elasticsearch and
MongoDB instances** — many requiring no authentication — and a wave of "MongoDB apocalypse" ransom
attacks wiped or held them hostage at scale. The cause was almost never an exploit. It was one ingress
rule, opened "temporarily" for a migration or a demo, that allowed the world to reach a port that should
have been reachable only from an app subnet.

The same year, **Capital One** lost ~100M records — and the network layer is a quiet co-defendant in
that chain. The headline is SSRF and an over-broad IAM role (you ruled on that in Module 01), but the
WAF was an internet-facing host *allowed to make outbound calls to the metadata service and onward to
S3*. A tighter egress posture and tighter segmentation around that host would have shortened, or broken,
the chain. The network controls didn't cause the breach, but they were the failed *containment* — the
walls that should have stopped a foothold from becoming an exfiltration.

So before you read on, this module turns on one question about the most boring-looking object in the
cloud — a Security Group ruleset:

> **Given a set of Security Groups, what is actually reachable from the internet?**

## Your job

By the end of this module you'll **audit a cloud network for reachability, then close it as code.** Map
The target account's VPC with `cloudmapper`, find the Security Groups that expose sensitive ports to
`0.0.0.0/0`, and trace the *transitive* paths an attacker actually walks. Then do the half auditing
skips: **author a corrected, default-deny Security Group baseline and re-verify that the bad paths are
gone while the app still works** — and encode the verdict as a scanner rule that fails the exposure and
passes the fix. Find → author the baseline → prove it holds: the exact motion of a cloud network review,
and the same shape you'll repeat with NetworkPolicies in Module 12.

## Call it before you read on

Don't scroll. Write your gut answers — under-counting reachability here is the teaching event, and
you'll grade yourself in the lab.

> **Q1.** An `app-sg` allows `:22` from `0.0.0.0/0`. A `db-sg` allows `:5432` *only* from `app-sg`. The
> database has no public IP and lives in a private subnet. **Is the database reachable from the
> internet?**
>
> **Q2.** Your team audited *ingress* and found it clean — every sensitive port is locked down inbound.
> Has the network been secured against an attacker who already has a foothold on one instance?
>
> **Q3.** You count six Security Groups, each "mostly fine." Where does the real attack surface live —
> in the worst single rule, or somewhere the per-group review can't see?

## The reachability model, revealed

Hold your answers against these.

**Q1 — reachability is transitive, and the audit that counts rules misses it.** The database has no
public address and its own group only trusts `app-sg`. A per-rule scan calls it clean. But `app-sg`
exposes `:22` to the world — so an attacker reaches the app instance, lands a shell, and *from there*
is a member of `app-sg`, which the database explicitly trusts. The database **is** reachable from the
internet; just not in one hop. **The mental model: a Security Group is the stateful host firewall you've
written for years, but applied per-network-interface and composable — so reachability is a graph, not a
table.** You don't read down the rules; you ask "what can the internet touch, and what can *that* touch,"
following group-references like edges. People reliably under-count this, and the under-count is how a
"locked-down" database ends up one `ssh` away from `0.0.0.0/0`.

**Q2 — ingress is half the wall; the cloud's default egress is open.** On-prem, a default-deny
perimeter means nothing leaves unless you allow it. In a VPC, **all outbound traffic is permitted by
default** — an intentional developer-experience choice that means the exfiltration path Capital One's
WAF used was open out of the box. Locking down ingress stops the *initial* reach; it does nothing about
a foothold calling the metadata service, pivoting east-west to a peer, or shipping data to an external
IP on 443. A real baseline scopes *egress* too — VPC Endpoints so S3/DynamoDB traffic never leaves the
AWS network, PrivateLink for third parties, restrictive egress rules for the rest — and treats "what
must this workload legitimately reach" as the question, in both directions.

**Q3 — the attack surface is the union of every rule, and it lives in the composition.** No single
group in the lab is catastrophic on its own — that's exactly why per-group review passes them. The
exposure is the *union*: `app-sg`'s open `:22` plus `db-sg`'s trust of `app-sg` is the chain; the
public ALB plus a missing egress rule is the exfil path. **Network security in the cloud is reasoning
about the whole reachable set, not auditing rules one at a time** — which is why the fix isn't "delete
the worst rule" but **author a default-deny baseline**: a group denies all ingress unless a rule
explicitly allows it, so least privilege means *only the rules the architecture provably needs*, nothing
"just in case." And because Security Groups are IAM-controlled API objects (Module 02), anyone with
`ec2:AuthorizeSecurityGroupIngress` can re-punch the hole — so the baseline only stays true if a guardrail
re-checks it. That guardrail is this module's deliverable.

## Learn (~4 hrs)

*Richer than a foundations module: cloud networking re-defines words you already know, and the
reachability model carries into Kubernetes (Module 12). Read the case first, then the mechanism.*

**VPC and the firewall that isn't (~1.5 hrs)**
- [AWS — How Amazon VPC works](https://docs.aws.amazon.com/vpc/latest/userguide/how-it-works.html) (~40 min) — the authoritative tour of subnets, route tables, Internet/NAT gateways, Security Groups and NACLs. Read it for the vocabulary the lab assumes; note which objects are control-plane (API-managed) versus data-plane.
- [AWS — Security Groups vs Network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Security.html) (~20 min) — the stateful-SG vs. stateless-NACL distinction and the default-permit-egress fact. This is the "host firewall, per-ENI, composable" mental model in primary-source form.
- [AWS — control traffic with VPC Endpoints / PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html) (~20 min, skim) — why keeping AWS-service and third-party traffic off the public internet is the egress baseline, not a nicety.

**The exposure wave, from the source (~1 hr)**
- [Shodan — Elastic data exposure grows to 3.2 PB](https://blog.shodan.io/elastic-data-exposure-grows-to-3-2-pb/) (~20 min, orient) — Shodan's own 2018→2020 measurement of internet-exposed Elasticsearch/MongoDB/HDFS instances; the 2017–19 wave never fully ended.
- [Krebs on Security — the MongoDB ransom wave](https://krebsonsecurity.com/2017/01/extortionists-wipe-thousands-of-databases-victims-who-pay-up-get-stiffed/) (~20 min) — contemporaneous reporting on the `0.0.0.0/0`-exposed-DB ransom attacks; corroborate the scale.
- [US Senate report — Capital One](https://www.hsgac.senate.gov/wp-content/uploads/imo/media/doc/Capital%20One%20Report.pdf) (~20 min, skim the network/WAF section) — re-read the chain with the network-containment lens: which walls were the network's job?

**Mapping reachability (~1.5 hrs)**
- [cloudmapper — README](https://github.com/duo-labs/cloudmapper) (~30 min) — Duo Labs' topology mapper. Read the `collect → prepare → audit → webserver` workflow; `audit` is what surfaces the `0.0.0.0/0` findings, the graph is what communicates them.
- [AWS — VPC Flow Logs (record format)](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) (~30 min) — read the "Flow log records" section; the 5-tuple + ACCEPT/REJECT is how reachability is *observed* after the fact (scans = REJECT storms, exfil = a fat 443 flow to an external IP). You'll parse these in the lab.
- [Checkov — AWS Security Group policies](https://www.checkov.io/5.Policy%20Index/terraform.html) (~20 min, skim) — find the built-in rules that fail `0.0.0.0/0` on sensitive ports (e.g. CKV_AWS_24/25 for 22/3389); this is the guardrail you'll own.

## Key concepts
- A Security Group **is** the stateful host firewall you know — but per-ENI and composable, so reachability is a graph (follow group-references as edges), not a per-rule table
- Transitive reach: a private DB that only trusts `app-sg` is internet-reachable if `app-sg` is internet-reachable — auditing rules one at a time misses this
- The attack surface is the **union** of every rule; the exposure usually lives in the composition, not the single worst line
- VPC egress is **default-permit** — locking ingress doesn't stop exfiltration; a real baseline scopes egress with VPC Endpoints / PrivateLink / restrictive rules
- Default-deny baseline: only the rules the architecture provably needs; "just in case" rules are the exposure
- Security Groups are IAM-controlled objects (Module 02) — the baseline only holds if a scanner re-checks it, which is why the fix ends in code

## AI acceleration
Paste a Security Group set and ask a model "what's reachable from the internet, and what can each
reachable host then reach?" It's a strong first-pass — it'll flag the `0.0.0.0/0` on `:22` immediately.
But it reads the rules as a list, and reachability is a graph: it routinely misses the *transitive* hop
(internet → `app-sg` → the database that trusts `app-sg`) and it can't know whether a route table or
private subnet actually makes a path live. Treat its output as a hypothesis and confirm each path against
the topology — `cloudmapper`'s graph and your reachability check are ground truth, the model is the
draft. The skill it can't do for you is **authoring the minimum default-deny baseline** that closes the
reachable paths without breaking the app, and proving the cut. You direct it; you own the baseline.
