# Module 12 — Kubernetes — RBAC & Network Policy

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *in Kubernetes, the IAM is the cluster; getting RBAC wrong is a blast-radius problem, not an account problem.*

## Why this matters
When Shopify, Tesla, and Capital One disclosed container/Kubernetes misconfigurations, the common thread was not a zero-day — it was `cluster-admin` ServiceAccounts accessible to workloads that should have had no API access at all. A pod that can call the Kubernetes API with broad permissions can list secrets, create privileged pods, modify RBAC, and lateral-move to cloud credentials via the instance metadata service. CIS Kubernetes Benchmark controls for RBAC are consistently among the highest-failure controls in enterprise audits. Meridian Financial's EKS migration revealed that their CI/CD system's ServiceAccount had `cluster-admin` — meaning a compromised CI pipeline could rewrite any workload in the cluster.

## Objective
Stand up a kind cluster, run `kube-bench` against it to identify CIS Benchmark failures, identify and exploit a misconfigured `cluster-admin` ServiceAccount, fix the binding with a least-privilege replacement, and write a NetworkPolicy that isolates a namespace.

## The core idea
Kubernetes RBAC has a conceptually simple model — Subjects (users, groups, ServiceAccounts) are bound to Roles (a list of `apiGroups`/`resources`/`verbs`) via RoleBindings — but the blast radius of mistakes is asymmetric. A Role that grants `get secrets` in `kube-system` can read every cluster credential. A ClusterRoleBinding to `cluster-admin` gives any pod bearing that ServiceAccount unrestricted API access across every namespace. The key insight for defense is that most workloads need *zero* Kubernetes API access: they read from their own mounted secrets, write to their own log streams, and never touch the API server. The default `default` ServiceAccount token is mounted into every pod unless you explicitly disable it — and many applications run for years without the team realising the token is there.

The audit starting point is the same pattern you know from cloud IAM: enumerate who has what, then ask "does this subject actually need this?" `kubectl auth can-i --list --as=system:serviceaccount:default:my-sa` shows the effective permissions of a ServiceAccount from inside or outside the cluster. `kube-bench` automates the CIS Kubernetes Benchmark checks — control-plane configuration, API server flags, etcd settings, RBAC posture — and produces a prioritised finding list. The CIS Benchmark is the closest thing to a universal hardening baseline for Kubernetes; section 5 (Policies) covers RBAC and Network Policy.

Network Policy in Kubernetes is opt-in and default-deny must be explicitly declared. Without a NetworkPolicy, every pod in the cluster can reach every other pod on any port — a flat network. A `default-deny-all` ingress NetworkPolicy for a namespace means only explicitly permitted traffic reaches pods; you build the allowlist from that baseline. This is the Kubernetes equivalent of a firewall default-deny rule. The `spec.podSelector: {}` (empty selector matches all pods) combined with `policyTypes: [Ingress]` and no `ingress:` rules achieves the deny; then individual policies open specific port/protocol combinations between labelled sets. The failure mode is partial coverage: policies in namespace A don't protect namespace B unless B also has a default-deny.

The practitioner discipline is **least-privilege + default-deny, verified**. RBAC changes should go through code review (the bindings are YAML, they live in git); `kubectl auth can-i` is the functional test. Network Policy changes should go through review and ideally a network-policy visualiser like Hubble or `np-viewer`. `kube-bench` in CI on cluster creation is the baseline check; `kube-bench` on a schedule is the drift detection. Meridian's team now runs kube-bench as a post-deployment check in their EKS cluster provisioning pipeline and fails the pipeline on any High finding with an available fix.

## Learn (~3.5 hrs)

**Kubernetes RBAC (~1.5 hrs)**
- [Kubernetes docs — Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) — the primary reference; read the "Role and ClusterRole", "RoleBinding and ClusterRoleBinding", and "ServiceAccount permissions" sections. The default ClusterRoles table is worth memorising.
- [NCC Group — "Attacking Kubernetes Clusters Through Your Network Plumbing"](https://research.nccgroup.com/2021/11/10/your-k8s-nodes-iam-clouds-in-the-sky/) — a practitioner read on how RBAC misconfigs compound with cloud IAM; the credential chain from pod → SA token → API server → cloud metadata is explained clearly.

**kube-bench (~0.5 hr)**
- [kube-bench GitHub README](https://github.com/aquasecurity/kube-bench) — read the README and the "Running kube-bench" section; understand which CIS controls it covers and how to interpret scored vs. unscored findings.

**Kubernetes Network Policy (~1 hr)**
- [Kubernetes docs — Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — the canonical reference; read "The NetworkPolicy resource" and the "Default policies" section to understand the opt-in model and default-deny pattern.
- [Ahmet Alp Balkan — "Kubernetes Network Policy Recipes"](https://github.com/ahmetb/kubernetes-network-policy-recipes) — a practical cookbook of real NetworkPolicy patterns (deny-all, allow-from-namespace, allow-specific-port); each recipe is a short YAML with an explanation. Use it as a reference during the lab.

**CIS Kubernetes Benchmark (~0.5 hr)**
- [CIS Kubernetes Benchmark — Controls overview (public summary)](https://www.cisecurity.org/benchmark/kubernetes) — download or read the public summary; section 5 (Policies) is the most directly relevant to RBAC and NetworkPolicy.

## Key concepts
- RBAC model: Subject → RoleBinding → Role (`apiGroups`/`resources`/`verbs`)
- ClusterRoleBinding vs. RoleBinding: cluster-wide vs. namespace-scoped
- Default ServiceAccount token is auto-mounted — opt out with `automountServiceAccountToken: false`
- `cluster-admin` ClusterRole = unrestricted API access; never bind workloads to it
- `kubectl auth can-i --list --as=` as the functional permission test
- NetworkPolicy is opt-in; no policy = flat network; `podSelector: {}` + no ingress = default-deny
- kube-bench CIS Benchmark sections 1–5; scored vs. unscored; High vs. Low
- MITRE ATT&CK T1078.004 (Valid Accounts: Cloud Accounts — SA tokens), T1613 (Container & Resource Discovery)

## AI acceleration
Paste a RoleBinding YAML into a model and ask it to identify the blast radius: what can this ServiceAccount do, what namespaces are affected, and what is the minimum Role that covers the legitimate use case? It's strong on RBAC YAML analysis. What it can't tell you is whether the ServiceAccount's token has been leaked or rotated — that requires checking the cluster state. Use the model to draft the least-privilege replacement Role; you validate it with `kubectl auth can-i` before applying.
