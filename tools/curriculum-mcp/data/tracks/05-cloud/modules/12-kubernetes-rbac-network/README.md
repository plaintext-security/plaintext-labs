# Module 12 — Kubernetes: RBAC & Network Policy

*Variant D · breach-driven, build-first / audit→build ("ship it open, then prove the cut holds"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *Kubernetes RBAC is cloud IAM again, but for the cluster — a ServiceAccount is a principal, a Role is a policy, and a default-allow pod network is the flat LAN you'd never ship on-prem.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4.5–6.5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 02 — Cloud Identity & IAM](../02-cloud-identity-iam/README.md) · [Module 04 — Cloud Network Security](../04-cloud-network-security/README.md)
{ .module-meta }


## The case

In February 2018, **RedLock's CSI team (now Palo Alto Unit 42)** found a **Kubernetes dashboard
belonging to Tesla, running on the public internet with no authentication** — anyone who found it could
issue commands to the cluster. Inside one of the pods, in plaintext, were **Tesla's AWS access
credentials.** The attackers used them to run a **cryptojacking** operation on Tesla's cloud
infrastructure, going to some lengths to hide it (a private mining pool, traffic behind CloudFlare, low
CPU usage to stay under the radar). This is the canonical container breach shape — **K8s misconfig →
cloud credentials → cloud compromise** — and almost none of it was an exploit. The dashboard was simply
open, and the pod's environment was simply readable.

That chain has two legs you'll build the defense for in this module. The first leg is *who inside the
cluster can read what* — RBAC. The second is *which pod can reach which pod* — Network Policy. Tesla lost
on both: an unauthenticated principal reached the API, and a pod handed up cloud keys it had no business
holding where anything could read them.

## Your job

This is a **build-first** module: you'll stand up a real cluster, **ship it the way Tesla shipped it**
(an over-broad ServiceAccount bound to `cluster-admin`, a flat pod network), prove what that costs, and
then **author the fix as code** — a least-privilege Role + RoleBinding and a default-deny NetworkPolicy —
and **re-verify** that the cut holds. The artifact you walk away with is the thing a platform-security
engineer is paid for: RBAC and segmentation as reviewed YAML in git, plus a check that *fails* the
over-broad binding before it ever merges.

## The model: it's IAM, one layer down

You already know this model — you wrote it for AWS in module 02. Kubernetes RBAC is the same evaluation,
relabelled for the cluster:

| Cloud IAM (module 02) | Kubernetes RBAC |
|---|---|
| Principal (user / role) | **Subject** (user, group, **ServiceAccount**) |
| Policy (`Action` × `Resource`) | **Role / ClusterRole** (`verbs` × `resources` × `apiGroups`) |
| Attaching a policy to a principal | **RoleBinding / ClusterRoleBinding** |
| `Resource: "*"` / `Action: "*"` | `cluster-admin`, or `verbs: ["*"]` on `["*"]` |
| Trust policy (who can assume) | the SA **token**, auto-mounted into every pod |

The one difference that bites is the **default**. In AWS, a new principal can do *nothing* until you
grant it. In Kubernetes, every pod gets the `default` ServiceAccount's token **auto-mounted at
`/var/run/secrets/...` unless you explicitly say `automountServiceAccountToken: false`** — so a
compromised process always has *a* token to the API server, whether the app uses it or not. Bind that SA
to anything broad and you've handed the attacker the cluster. `cluster-admin` is the `Resource: "*"` of
Kubernetes: it can read every Secret in every namespace — which, in the Tesla shape, is where the cloud
keys live.

The network half is the same story in a different plane. **Kubernetes ships with a flat pod network:
with no NetworkPolicy, every pod can reach every other pod on every port, across namespaces.** That is
the default-allow LAN you would never deploy on-prem — and NetworkPolicy is *opt-in*, so the segmentation
doesn't exist until you declare it. A `default-deny` policy (`podSelector: {}`, `policyTypes: [Ingress]`,
no `ingress:` rules) is the firewall default-deny you've written for years (module 04); you then add back
the specific flows the app actually needs. The failure mode is partial coverage — a deny in namespace `A`
does nothing for namespace `B` unless `B` has its own.

**One thing to call before you build.** A pod in your cluster gets compromised — say through an app RCE.
*Before reading on, write down: by default, what can that pod reach, and what can its ServiceAccount
read?* The honest default answers are why this module exists: it can reach **every other pod in the
cluster** (flat network), and its token can do **whatever its SA is bound to** — and far more often than
teams expect, that SA is over-broad enough to read Secrets that include cloud credentials. You'll prove
both in the lab, then take them away.

The practitioner discipline is **least-privilege + default-deny, *verified*.** RBAC and NetworkPolicy are
YAML, so they go through code review and live in git; `kubectl auth can-i` is the functional test for the
RBAC cut, and a connectivity probe is the test for the network cut. `kube-bench` (the CIS Kubernetes
Benchmark, section 5 covers RBAC and policies) is the baseline audit and, run in CI, the drift detector.

## Learn (~3.5 hrs)

*Build-first module — read enough to write correct RBAC and NetworkPolicy, then go build. The bridge
(it's IAM again) is above; these carry the mechanism and the breach detail.*

**The anchor (~30 min)**
- [CyberScoop — Tesla falls victim to cryptomining scheme (RedLock's finding)](https://cyberscoop.com/tesla-cryptomining-redlock-cloud-breach/) (~15 min) — reporting on RedLock's discovery: an open Kubernetes console exposed AWS S3 credentials, which attackers used to mine cryptocurrency behind deliberate evasion. Read for the *shape* — open dashboard → cloud creds → abuse — which you'll rebuild.
- [k8s.af — Kubernetes Failure Stories](https://k8s.af/) (~15 min, browse) — the community catalogue of real K8s post-mortems; skim for how often "open API / over-broad SA / flat network" recurs.

**Kubernetes RBAC (~1.5 hrs)**
- [Kubernetes docs — Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) (~45 min) — the primary reference; read "Role and ClusterRole", "RoleBinding and ClusterRoleBinding", and "ServiceAccount permissions". The default ClusterRoles table is worth memorising.
- [NCC Group — Deep Dive into Real-World Kubernetes Threats](https://www.nccgroup.com/research-blog/deep-dive-into-real-world-kubernetes-threats/) (~30 min) — a practitioner walkthrough of the RBAC half of the chain: a compromised pod's service-account token → the API server → namespace traversal → cluster-wide takeover. The mechanics behind "over-broad SA + flat cluster = one credential path."

**Network Policy & kube-bench (~1 hr)**
- [Kubernetes docs — Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) (~25 min) — read "The NetworkPolicy resource" and "Default policies" for the opt-in / default-deny model.
- [Ahmet Alp Balkan — Network Policy Recipes](https://github.com/ahmetb/kubernetes-network-policy-recipes) (~20 min, reference) — short, working YAML for deny-all, allow-from-namespace, allow-port; keep it open during the lab.
- [kube-bench README](https://github.com/aquasecurity/kube-bench) (~15 min) — what CIS controls it covers and how to read scored vs. unscored, FAIL vs. WARN.

## Key concepts
- RBAC *is* cloud IAM for the cluster: Subject → Binding → Role (`verbs` × `resources` × `apiGroups`); `cluster-admin` is the `Resource:"*"`
- The SA token is **auto-mounted into every pod** unless `automountServiceAccountToken: false` — a compromised process always has *a* key to the API
- `cluster-admin` on a workload SA = read every Secret in every namespace = the Tesla "cloud creds in a pod" path
- `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>` is the functional permission test (the K8s `simulate-principal-policy`)
- NetworkPolicy is **opt-in**; no policy = flat network across namespaces; `podSelector: {}` + no `ingress:` = default-deny, then add back specific flows
- Partial coverage is the trap: a deny in one namespace protects only that namespace
- kube-bench / CIS section 5 audits RBAC + policies; least-privilege + default-deny only count when *verified*
- MITRE ATT&CK: T1078.004 (Valid Accounts: Cloud Accounts — SA tokens), T1525/T1610 (container deployment), T1613 (Container & Resource Discovery)

## AI acceleration
Paste a `ClusterRoleBinding` or a Role YAML into a model and ask for the blast radius — what this SA can
do, which namespaces it touches, and the minimum Role that covers the legitimate job. It's genuinely
strong at reading RBAC YAML and drafting a tighter Role. Two things it can't do for you: it can't see
*cluster state* — whether that SA's token has actually leaked, whether a NetworkPolicy already constrains
the pod — and it will happily write a NetworkPolicy that *looks* right but leaves a namespace uncovered.
So the model drafts; you **validate the RBAC cut with `kubectl auth can-i` and the network cut with a real
connectivity probe** before you trust either. AI authors → you review → you own the cut.
