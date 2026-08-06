# Lab 04 — Reachability, Then a Default-Deny Baseline: Audit the Network, Build the Fix, Prove It

> **Hands-on lab.** Environment: `plaintext-labs/cloud/04-cloud-network-security` (a bundled account
> **snapshot** + `cloudmapper` + Python — no cloud account, no live VPC). Objective: **prove what the
> internet can actually reach in a VPC — including the *transitive* path a per-rule audit misses — then
> author a default-deny Security Group baseline and prove the cut holds.** Target: **~90 min**, one
> finish line.

*Variant D · breach-driven, audit→build→re-verify. [← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **A Security Group *is* the stateful host firewall — per-ENI, composable.** | Reachability is a **graph**: follow group-references as edges, don't read a rule list top to bottom. |
| 2 | **Reach is transitive.** | A private DB that only trusts `app-sg` is internet-reachable the moment `app-sg` is — internet → `app:22` → the DB. |
| 3 | **Stateful means egress is default-permit.** | A clean *ingress* audit does nothing about a foothold shipping data out on 443 or calling the metadata service. |
| 4 | **The attack surface is the *union* of every rule.** | No single group here is catastrophic alone — the exposure lives in the composition, not the worst single line. |
| 5 | **Default-deny baseline = only the rules the architecture provably needs.** | The fix isn't "delete the worst rule"; "just in case" rules *are* the exposure. |
| 6 | **Security Groups are IAM-controlled API objects.** | Anyone with `ec2:AuthorizeSecurityGroupIngress` can re-punch the hole — the baseline only holds if a scanner re-checks it. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [reachability model, revealed](README.md#the-reachability-model-revealed) and the
> [SG vs NACL table](README.md#the-reachability-model-revealed).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. `app-sg` allows `:22` from `0.0.0.0/0`; `db-sg` allows `:5432` **only** from `app-sg`, and the DB has
   no public IP. Is the database reachable from the internet — and why does a per-rule scan call it clean?
2. Your ingress audit comes back spotless. Name the *other* direction a real baseline has to scope, and
   why locking ingress alone leaves the Capital One exfil path open.

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs `cloudmapper` and
two small Python analyzers against a bundled AWS account JSON snapshot and VPC flow log — no cloud
account or real credentials required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/04-cloud-network-security
make up                  # build the container (cloudmapper + Python)
make demo                # worked SG audit + flow log + the reachability before/after loop
make shell               # drop into the container to work interactively
# individual targets:
make audit               # cloudmapper audit against the bundled account JSON
make flows               # VPC flow-log anomaly analysis (scan + exfil)
make reachability        # reachability check vs the ORIGINAL groups — expect 2 FAILs
make reachability-fixed  # reachability check vs YOUR security-groups-fixed.json — aim for all PASS
make down                # stop when done
```

Two data sets are bundled under `data/`: **`account/target/`** — an account JSON snapshot (the output of
`cloudmapper collect`) of the `financial-prod` VPC (`10.0.0.0/16`: a public ALB subnet, a private app
subnet, a private db subnet), and **`vpc-flow-logs.log`** — representative flow records including normal
traffic, a port scan, and a suspicious large transfer. A reference remediation,
`account/target/security-groups-fixed.json`, ships too — treat it as the answer key you check *against*
after you've authored your own.

**What this lab is — and isn't (read this).** You audit a *static account snapshot*, not a live VPC —
there's no instance to SSH into and nothing to attack on the wire. That's deliberate: the skill is
**reachability reasoning and the fix**, not packet-level exploitation. "What's reachable" is *computed*
from the Security Group graph, the way `cloudmapper audit` and a reachability check do it — a logical
evaluation, not a live scan. One honest seam to keep in view: `check_reachability.py` evaluates the
**SG rules only**, so it reports `internet → app:22` as `ALLOW` even though the app sits in a *private
subnet with no public IP* — real `cloudmapper` folds in route tables and public-IP assignment. The SG
finding is a defense-in-depth verdict ("this rule should not exist"); the routing is the second question
the graph answers. Honest tool, honest answer.

> **▸ On track if:** `make demo` prints the SG audit — `[INFO] alb-sg`, `[HIGH] app-sg` (port 22),
> `[CRITICAL] db-sg` (port 5432), **`Total HIGH/CRITICAL findings: 2`** — then the reachability loop:
> the ORIGINAL groups show **`2 assertion(s) FAILED`** and the fixed groups **`All reachability
> assertions PASS`**. The snapshot is live.

> **Authorization note.** Only test systems you own or have explicit written permission to test.
> Everything here runs locally against bundled data you own — no real AWS account, no real IPs.

---

## Scenario

The `financial-prod` infrastructure team hands you an account JSON export and a week of VPC flow logs.
They've had two scares: a third-party threat feed flagged an unexpected outbound connection, and a
compliance reviewer flagged Security Groups with `0.0.0.0/0` ingress. Your deliverable is a
**reachability finding plus the fix**: prove what the internet can actually touch (including
transitively), then author a default-deny Security Group baseline that closes it without breaking the
app, and prove the cut holds.

Each step runs the same rhythm: **Predict** (commit before you look) → **Do** (gather/prove the
evidence) → **Reveal** (check your call) → **Record** (one line in the report).

---

## Build it — read a little, do a little

### Step 1 — Audit the ingress: what does the world touch directly?

**Concept (30 sec):** Flight-card #4. Run the audit and list *every* `0.0.0.0/0` finding — then split
the intentional (the public ALB) from the misconfiguration (a DB on the open internet). The attack
surface is the union, so you catalogue all of them before judging any.

**Predict, then do:** how many groups expose a *sensitive* port to `0.0.0.0/0`, and which ports? Then run
`make audit` (or `make demo`) and read `data/account/target/describe-security-groups.json`.

> **▸ On track if:** you find **three** `0.0.0.0/0` ingress groups but only **two findings**: `alb-sg`
> (`sg-00000001`) on `443`/`80` is **intended** (`[INFO]`); `app-sg` (`sg-00000002`) on `:22` is `[HIGH]`;
> `db-sg` (`sg-00000003`) on `:5432` is `[CRITICAL]`. **Record:** the raw ingress findings, tier, and
> intentional-vs-misconfig for each.

### Step 2 — Trace the transitive reach: the hop the audit doesn't draw

**Concept (30 sec):** Flight-card #2. `db-sg` also carries a *legitimate* rule — `:5432` from `app-sg`
only — and the DB has no public IP, so that rule *looks* private. But `app-sg` is internet-exposed on
`:22`, and an attacker on the app instance **is a member of `app-sg`**, which `db-sg` trusts.

**Predict, then do:** is the database reachable from the internet by a path *other* than its own
`0.0.0.0/0` rule? Read the `UserIdGroupPairs` in `describe-security-groups.json` and follow the edge.

> **▸ On track if:** you can state the chain in one sentence — **internet → `app-sg :22` → the app
> instance → member of `app-sg`, which `db-sg` trusts → the DB.** Reachability is a graph; follow the
> group-reference edge. **Record:** the transitive path, not just the two direct ingress rules.

### Step 3 — Read the flow logs: the scan and the exfil the rules can't show

**Concept (30 sec):** Flight-card #3. Rules say what *may* flow; VPC Flow Logs record what *did*. A scan
is a burst of `REJECT`s from one source across many ports; an exfil is a fat `ACCEPT`ed flow to an
external IP on 443 — and nothing had to *allow* that egress, because VPC egress is default-permit.

**Do it:** run `make flows` (`analyze_flows.py data/vpc-flow-logs.log`), or open the log directly.

> **▸ On track if:** the analyzer reports a **port-scan candidate** — one external source IP with many
> `REJECT` flows across many destination ports — and a **large-transfer candidate**: an internal source
> sending **>10 MB to an external (non-RFC-1918) IP on 443**. **Record:** the scan source/target, and the
> exfil source→destination + byte count + the missing egress control. This is the Capital One containment
> gap in miniature — no ingress rule stopped it because none had to.

### Step 4 — See the gap as reachability (the audit, as something a machine checks)

**Concept (30 sec):** Flight-card #1. Finding the bad rule is the audit; *closing the loop* means
expressing "who must / must not reach whom" as assertions a checker can verify.

**Do it:** run `make reachability` — `check_reachability.py` evaluates the SG graph against the target's
required reachability matrix.

> **▸ On track if:** exactly two assertions **FAIL** — `internet -> app :22` and `internet -> db :5432`
> both show `ALLOW (want DENY)` — and the checker prints **`2 assertion(s) FAILED`** and exits non-zero.
> The legitimate paths (`internet -> ALB :443`, `ALB -> app :8080`, `app -> db :5432`) already PASS.
> **Record:** your audit finding is now a machine-checkable claim.

### Step 5 — Author the corrected, default-deny baseline

**Concept (30 sec):** Flight-card #5. Default-deny means *only the rules the architecture provably
needs* — nothing "just in case." Copy `describe-security-groups.json` to `security-groups-fixed.json`
and rewrite it to the minimum:

- **`app-sg :22`** — replace `0.0.0.0/0` with the **bastion subnet** CIDR (`10.0.100.0/24`), not the world.
- **`db-sg :5432`** — **remove** the `0.0.0.0/0` rule entirely; keep only the `app-sg`-referenced rule.
- **Scope egress** — don't lean on default-permit-out: allow only what each tier needs (app → db:5432, app
  → 443 to a VPC-endpoint/known range), so the Step-3 exfil path has no rule to ride.
- **Leave intact** the intentional public ALB (`443`/`80`) and the group-referenced flows (`alb-sg`→app,
  app→`db-sg`).

> **▸ On track if:** your fixed file has *no* `0.0.0.0/0` on `:22` or `:5432`, keeps both
> `UserIdGroupPairs` rules, and — a good sanity check — reads like the reference
> `data/account/target/security-groups-fixed.json` you can diff against afterward. **Record:** the
> before/after for each changed rule.

---

## Prove the control (your finish line)

Reachability is only "fixed" when you can **re-verify** it and the guardrail *flips*. Two moves, one bar:

1. **The reachability check goes green.** Run `make reachability-fixed` against *your*
   `security-groups-fixed.json`. Every assertion must PASS — the checker prints **`All reachability
   assertions PASS`** and **exits 0**: `internet -> app:22` and `internet -> db:5432` now `DENY`, the
   transitive internet→db path is gone, and `ALB -> app:8080` / `app -> db:5432` still `ALLOW`. If a
   legitimate path broke, you over-tightened — that feedback loop *is* the change review.
2. **The scanner rule flips.** Your `Automate & own it` rule (below) **fails** the original ruleset
   (exit non-zero) and **passes** your fix (exit zero). If it doesn't flip, the verdict isn't yet code.

Capture the before/after in `findings.md`, then score your three README "Call it" predictions against the
reveals; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. State the transitive internet→database path in one sentence — and why a per-rule audit misses it.
2. Your ingress is locked down. What direction is *still* open by default, and what did it cost Capital One?
3. Across six "mostly fine" groups the surface lives in the composition. Why does that make the fix
   "author a default-deny baseline," not "delete the worst rule"?

---

## Deliverables

- **`findings.md`** — a network findings report: the topology/Security-Group findings (with the
  **transitive** path called out), the flow-log findings (scan source/target, exfil candidate + byte
  count), a recommended control per finding, and the **before/after reachability output**.
- **`security-groups-fixed.json`** — your default-deny baseline that makes `check_reachability.py` exit 0.

Commit both. *Do not commit real credentials, real account IDs, or any real IPs / flow logs from live
infrastructure* — the bundled data is synthetic and safe; your own captures are not.

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your verdict is "a Security Group must never
expose a sensitive port to `0.0.0.0/0`, and the reachable set must match the baseline." Encode it two ways:

1. **A scanner rule.** Write (or enable and configure) a **Checkov/tfsec-style policy** that **fails** any
   Security Group allowing `0.0.0.0/0` ingress on a sensitive port (22, 3389, 5432, 3306, 9200, 27017) and
   **passes** the scoped baseline. Run it against the original ruleset (must exit non-zero) and your fix
   (must exit zero) and show it flips.
2. **The reachability assertion** (`check_reachability.py`, already in the lab): given a Security Group
   set it computes the reachable graph and asserts the required-DENY paths are unreachable and the
   required-ALLOW paths reachable — exit non-zero on the broken groups, exit zero on the baseline. Extend
   its matrix if your fix adds a tier.

Have a model draft both; review every line and confirm each **fails the original for the right reason**
(the actual `0.0.0.0/0`-on-22 rule and the transitive path, not an unrelated nit). Then paste your rule
back and ask the model to write a Security Group that *sneaks past* — an IPv6 `::/0`, a
`0.0.0.0/1`+`128.0.0.0/1` split, a port range that straddles 22. If it finds one, your rule is too
narrow. This is your verdict made un-recurrable — and the same pattern returns as the NetworkPolicy you
author in Module 12.

## Definition of done (`cloud-network-security` ✅)

- [ ] `make audit` findings listed: every `0.0.0.0/0` group, its tier, and intentional (public ALB) vs.
  misconfiguration (SSH/DB to the world).
- [ ] You can state the **transitive** internet→database path in one sentence — and why a per-rule audit
  misses it.
- [ ] You identified the port-scan source/target and the large-transfer exfil candidate from the flow
  logs, and named the missing egress control.
- [ ] `make reachability` FAILs two assertions on the original groups; `make reachability-fixed` shows
  **all PASS (exit 0)** on your `security-groups-fixed.json` — bad paths DENY, `ALB→app` and `app→db`
  still ALLOW.
- [ ] Your scanner rule **fails the original, passes the fix**.
- [ ] You scored your three README "Call it" predictions against the reveals, and can explain all six
  flight-card facts cold.

## Connects forward

The reachability-as-graph and default-deny-baseline motion here is exactly **Module 12 (Kubernetes — RBAC
& Network Policy)**, where the same fix is a `NetworkPolicy` instead of a Security Group. The `0.0.0.0/0`
findings are what **Module 05 (Posture & Misconfiguration Auditing)** catches at scale with `prowler
check aws_ec2_securitygroup_allow_ingress_from_internet_to_any_port`, and the scanner rule you wrote is
the **Module 06 (IaC Security)** CI gate applied to network config. The flow-log analysis reappears in
**Module 16 (Cloud Incident Response)**, correlated with CloudTrail to reconstruct a timeline.

## Marketable proof

> "Given a cloud network, I audit reachability with cloudmapper — including the *transitive* internet→DB
> paths a per-rule review misses — then author a default-deny Security Group baseline and prove with a
> reachability check and a Checkov rule that the bad paths are closed and the app still works."

## Stretch

- Wire the scanner rule and the reachability check into a **CI gate** that runs on every change to the
  groups file and fails the build if any required-DENY path is reachable — the shift-left idea from Module 06.
- Run `cloudmapper webserver` in the container and open the interactive graph (forward port 8000); find
  which subnet is directly internet-routable and confirm the routing story from the "what this lab isn't"
  note visually.
- Extend the flow-log analyzer to enrich flagged external IPs against the AWS IP-range JSON
  (`https://ip-ranges.amazonaws.com/ip-ranges.json`) and mark which are AWS-owned vs. truly external.
