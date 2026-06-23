# Lab 04 — Reachability, Then a Default-Deny Baseline: Audit the Network, Build the Fix, Prove It

*Variant D · breach-driven, audit→build→re-verify. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs `cloudmapper`
against a bundled AWS account JSON snapshot and provides realistic VPC flow logs for analysis — no
cloud account or real credentials required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/04-cloud-network-security
make up         # build the container (cloudmapper + Python)
make demo       # worked Security Group audit + flow log walkthrough
make shell      # drop into the container to work interactively
make down       # stop when done
```

Two data sets are bundled: `data/account/target/` — an account JSON snapshot (the output of
`cloudmapper collect`) of the target account's VPC topology — and `data/vpc-flow-logs.log`, 50 representative
flow records including normal traffic, a port scan, and a suspicious large transfer.

**What this lab is — and isn't (read this).** You audit a *static account snapshot*, not a live VPC —
there's no instance to SSH into and nothing to attack on the wire. That's deliberate: the skill is
**reachability reasoning and the fix**, not packet-level exploitation. "What's reachable" is computed
from the Security Group graph and the topology, the way `cloudmapper audit` and a reachability check do
it — a logical evaluation, not a live scan. Honest tool, honest answer.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against bundled data you own — no real AWS account, no real IPs.

## Scenario
The target account's infrastructure team hands you an account JSON export and a week of VPC flow logs.
They've had two scares: a third-party threat feed flagged an unexpected outbound connection, and a
compliance reviewer flagged Security Groups with `0.0.0.0/0` ingress. Your deliverable is a **reachability
finding plus the fix**: prove what the internet can actually touch (including transitively), then author
a default-deny Security Group baseline that closes it without breaking the app, and prove the cut holds.

Each step runs the same rhythm: **Predict** (commit before you look) → **Do** (gather/prove the
evidence) → **Reveal** (check your call) → **Record** (one line in the report).

## Do

### Part 1 — Predict the reach, then prove it

1. [ ] **Map the topology.** Run the audit (`make audit`, or
   `cloudmapper audit --account  --config data/config.json`). **Predict** first: how many groups
   expose a sensitive port to `0.0.0.0/0`, and which ports? **Reveal:** the audit flags `0.0.0.0/0`
   ingress on `app-sg :22` and `db-sg :5432`, plus the intentional public ALB on 80/443. **Record:** the
   raw ingress findings.

2. [ ] **Trace the transitive reach — the hop the audit doesn't draw.** Read the groups in
   `data/account/target/describe-security-groups.json`. `db-sg` allows `:5432` only from `app-sg`, and
   the DB has no public IP — *looks* private. **Predict:** is the database reachable from the internet?
   **Reveal:** yes — internet → `app-sg :22` → the app instance → it's a member of `app-sg`, which
   `db-sg` trusts. Reachability is a graph; follow the group-reference edge. **Record:** the transitive
   path, not just the two ingress rules.

3. [ ] **Find the scan in the flow logs.** Open `data/vpc-flow-logs.log` (or run `make flows`). Find the
   port-scan signature — many `REJECT` flows from one source IP to many destination ports. **Record:**
   the source IP and the target it was sweeping.

4. [ ] **Find the exfil candidate, and tie it to a group.** Locate the large-transfer flow (>50 MB to an
   external IP on 443). **Predict:** is egress to 443 *explicitly allowed*, or open by default? **Reveal:**
   VPC egress is default-permit — nothing in the groups had to allow it. **Record:** source internal IP,
   external destination, byte count, and the missing egress control. This is the Capital One containment
   gap in miniature.

### Part 2 — Author the default-deny baseline, and prove it holds

Finding the exposure is the audit; **closing it without breaking the app is the fix** — and reachability
is only "fixed" when you can re-verify it.

5. [ ] **See the gap as reachability.** Run `make reachability` — the checker (`check_reachability.py`)
   encodes the target account's requirements as a matrix of who-must / who-must-not reach whom and reports
   PASS/FAIL. Two assertions FAIL: `internet → app:22` and `internet → db:5432` show `ALLOW` where the
   policy wants `DENY`. This is your audit finding, expressed as something a machine can check. *(If your
   lab build doesn't ship this target yet, the checker is the first thing you write in "Automate & own
   it" — write it, then come back.)*

6. [ ] **Author the corrected, default-deny baseline.** Copy
   `data/account/target/describe-security-groups.json` to `security-groups-fixed.json` and rewrite it
   to the minimum the architecture needs:
   - `app-sg :22` — replace `0.0.0.0/0` with the **bastion subnet** CIDR (`10.0.100.0/24`), not the world.
   - `db-sg :5432` — **remove** the `0.0.0.0/0` rule entirely; keep only the `app-sg`-referenced rule.
   - Add **scoped egress**: don't rely on default-permit-out; allow only what each tier needs (app → db:5432, app → 443 to a VPC-endpoint/known range), so the exfil path in step 4 has no rule to ride.
   - Leave the intentional public ALB (80/443) and the group-referenced flows (ALB→app, app→db) intact.
   Default-deny means *only the rules the architecture provably needs* — nothing "just in case."

7. [ ] **Re-verify reachability.** Run `make reachability-fixed`. Every assertion must PASS: `internet →
   app:22` and `internet → db:5432` now `DENY`, the transitive internet→db path is gone, and the
   legitimate ALB→app and app→db paths still `ALLOW`. If a legitimate path broke, you over-tightened —
   that feedback loop *is* the change review. Capture the before/after in `findings.md`.

## Success criteria — you're done when
- [ ] You listed every Security Group `cloudmapper audit` flags, the attached tier, and whether the
  exposure is intentional (public ALB) or a misconfiguration (DB to the world).
- [ ] You can state the **transitive** internet→database path in one sentence — and why a per-rule audit
  misses it.
- [ ] You identified the port-scan source/target and the large-transfer exfil candidate from the flow
  logs, and named the missing egress control.
- [ ] Your `security-groups-fixed.json` makes the reachability check exit 0: the two internet-facing
  findings and the transitive path now DENY, while ALB→app and app→db still ALLOW.
- [ ] You scored your three "Call it" predictions from the README against the reveals.

## Deliverables
`findings.md` — a network findings report: the topology/Security-Group findings (with the transitive
path called out), the flow-log findings (scan, exfil candidate), a recommended control per finding, and
the before/after reachability output. `security-groups-fixed.json` — your default-deny baseline that
passes the checker. Commit both. Do not commit real credentials, real account IDs, or real IPs from live
infrastructure.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your verdict is "a Security Group must never
expose a sensitive port to `0.0.0.0/0`, and the reachable set must match the baseline." Encode it two ways:

1. **A scanner rule.** Write (or enable and configure) a **Checkov/tfsec-style policy** that **fails** any
   Security Group allowing `0.0.0.0/0` ingress on a sensitive port (22, 3389, 5432, 3306, 9200, 27017)
   and **passes** the scoped baseline. Run it against the original ruleset (must exit non-zero) and your
   fix (must exit zero) and show it flips.
2. **The reachability assertion** (`check_reachability.py`) from Part 2: given a Security Group set, it
   computes the reachable graph and asserts the required-DENY paths are unreachable and the required-ALLOW
   paths reachable — exit non-zero on the broken groups, exit zero on the baseline.

Have a model draft both; review every line and confirm each **fails the original for the right reason**
(the actual `0.0.0.0/0`-on-22 rule and the transitive path, not an unrelated nit). This is your verdict
made un-recurrable — and the same pattern returns as the NetworkPolicy you author in Module 12.

## AI acceleration
Paste the full `data/vpc-flow-logs.log` and ask a model which entries indicate a port scan and which a
potential exfiltration, with the indicators. Compare against your own analysis and your checker. Then
paste the Security Group set and ask "what's reachable from the internet?" — note whether it catches the
**transitive** internet→db hop (it usually doesn't). Finally, paste your scanner rule and ask it to write
a Security Group that *sneaks past* — an IPv6 `::/0`, a `0.0.0.0/1`+`128.0.0.0/1` split, a port range that
straddles 22. If it finds one, your rule is too narrow.

## Connects forward
The reachability-as-graph and default-deny-baseline motion here is exactly Module 12 (Kubernetes — RBAC
& Network Policy), where the same fix is a `NetworkPolicy` instead of a Security Group. The `0.0.0.0/0`
findings are what Module 05 (Posture & Misconfiguration Auditing) catches at scale with `prowler check
aws_ec2_securitygroup_allow_ingress_from_internet_to_any_port`, and the scanner rule you wrote is the
Module 06 (IaC Security) CI gate applied to network config. The flow-log analysis reappears in Module 16
(Cloud Incident Response), correlated with CloudTrail to reconstruct a timeline.

## Marketable proof
> "Given a cloud network, I audit reachability with cloudmapper — including the *transitive* internet→DB
> paths a per-rule review misses — then author a default-deny Security Group baseline and prove with a
> reachability check and a Checkov rule that the bad paths are closed and the app still works."

## Stretch
- Wire the scanner rule and the reachability check into a CI gate that runs on every change to the groups
  file and fails the build if any required-DENY path is reachable — the shift-left idea from Module 06.
- Run `cloudmapper webserver` in the container and open the interactive graph (forward port 8000); find
  which subnet is directly internet-routable and confirm it visually.
- Extend the flow-log analyzer to enrich flagged external IPs against the AWS IP-range JSON
  (`https://ip-ranges.amazonaws.com/ip-ranges.json`) and mark which are AWS-owned vs. truly external.
