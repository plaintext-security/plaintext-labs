# Module 07 — Microsegmentation

*Type 7 · Build-&-Operate — stand up a default-deny segmentation policy in a real cluster and run it; the deliverable is the policy-as-code and its proven allow+deny pair, not an essay. (Secondary: Judgment-as-Code — the regression test that proves the denied path can't silently reopen.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *shrink the blast radius to a single service boundary, not a VLAN.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

On June 27, 2017, NotPetya entered Maersk through a poisoned update to Ukrainian accounting software on a single machine — and within a *minute or two* it had the entire global network. It spread two ways at once: **EternalBlue** (CVE-2017-0144, the SMBv1 RCE) hit every unpatched Windows host reachable on the internal network, and a Mimikatz-style credential dump plus pass-the-hash walked the rest using domain-admin tokens it found in memory. Maersk lost an estimated **$300 million**, rebuilt **4,000 servers and 45,000 PCs**, and ran on pen-and-paper for the better part of two weeks. The post-mortems converge on one root cause that has nothing to do with the exploit: the interior was **flat**. Any host could reach any other host, so a foothold on one box was a foothold on all of them. ([Wired's reconstruction](https://www.wired.com/story/notpetya-cyberattack-ukraine-russia-code-crashed-the-world/) is the canonical account.)

That is the case for microsegmentation, and it is not specific to NotPetya. Target 2013 followed the same arc: a stolen HVAC-vendor credential reached the corporate network, and from there a flat path led to the point-of-sale systems and 40 million cards. A misconfigured firewall rule, a leaked service-account token, or a container escape in one namespace is *one workload* if the network refuses east-west traffic by default — and the *whole blast radius* if it doesn't. In regulated environments (PCI-DSS, HIPAA, FedRAMP) auditors now ask specifically how you isolate cardholder data or PHI workloads from their neighbors in the *same* cluster; "we have a firewall at the edge" no longer scopes anything down.

## Objective

Deploy a default-deny Cilium network policy in a kind cluster that restricts database-tier access to backend pods only, prove the allow case (backend→db) and the deny case (frontend→db) with `kubectl exec`, watch the drop verdict in Hubble/`cilium monitor`, then try to pivot anyway — confirm the denied path stays denied under an active attempt — and encode the allow+deny pair as a regression test.

## The core idea

Microsegmentation is the **policy-as-code answer to the flat interior**: the network's default posture flips from *allow-all, block exceptions* to **deny-all, allow the minimum**, and that posture lives in version control as a declarative policy, not as a tangle of firewall rules someone maintains by hand. In Kubernetes the unit of segmentation is the workload, not the subnet: you label pods (`app: backend`, `tier: database`) and write a policy that says "pods labelled `tier: database` accept ingress *only* from pods labelled `app: backend`." Everything else is dropped because the policy exists at all — presence of an ingress rule on a pod is what makes its default deny. Crucially the rule is **label-scoped, not IP-scoped**: pod IPs churn on every restart, so IP rules rot constantly, while labels follow the workload. The policy *is* the perimeter now — there is no edge firewall doing this; the boundary is wherever the policy says it is.

The load-bearing judgment of this module is **default-deny then allow the minimum, and prove both halves.** Cilium is a CNI built on eBPF, which matters for one reason: enforcement happens in the kernel, on the sending node, *before* a packet leaves the container — not at a perimeter firewall downstream. There is no "go around the network boundary" because the boundary is the kernel hook every packet already traverses; a pod on the *same node* as the database still goes through it. That is what makes the deny credible enough to red-team. But a policy you only tested on the allow path is theater. The discipline — and the thing this module makes you do — is to verify the *deny* directly, then attempt to pivot around it (a different source pod, a relabel, a direct dial to the service IP) and confirm it still drops. A default-deny baseline you haven't tried to break is a guess.

Two gotchas decide whether this works in practice. First, **default-deny silently breaks DNS**: a strict deny that forgets to allow port 53 to kube-system kills name resolution for every governed pod, and the symptom looks like an application bug, not a network policy — so an explicit DNS allow is part of the baseline, not an afterthought. Second, **label scope is the soft spot**: `fromEndpoints: {app: backend}` allows *any* pod carrying that label, in any namespace; an attacker (or a careless teammate) who can schedule a pod with `app: backend` in some other namespace inherits the allow. Tightening the selector to require *both* the app label *and* the namespace is the difference between a policy that names a workload and one that names a string anyone can copy. The observability half closes the loop: Hubble and `cilium monitor` give a per-flow audit trail — "frontend tried database:80 at T, policy X dropped it" — correlated with pod/namespace/label metadata. That is the same structured telemetry module 09 turns into a lateral-movement detection.

## Learn (~3 hrs)

**Kubernetes NetworkPolicy fundamentals (~45 min)**
- [Kubernetes Network Policies (official docs)](https://kubernetes.io/docs/concepts/services-networking/network-policies/) (~25 min) — the canonical reference for the `NetworkPolicy` resource shape. Read "Behavior of `to` and `from` selectors" and "Default policies" closely; the rule that *a pod is default-deny only once a policy selects it* is the single most common source of "why is everything still open?"
- [Securing the network with Cilium and NetworkPolicy — the "Networkpolicy editor" mental model (Cilium docs)](https://docs.cilium.io/en/stable/security/policy/) (~20 min) — skim for `CiliumNetworkPolicy` vs. standard `NetworkPolicy` and the `fromEndpoints` selector; that selector is what you write in the lab.

**Why eBPF enforcement changes the threat model (~45 min)**
- [Cilium — eBPF datapath / how Cilium enforces policy](https://docs.cilium.io/en/stable/network/ebpf/intro/) (~25 min) — read enough to see *where* the drop happens (in-kernel, on the egress node) and why that means there is no path around the policy for a same-node pod. This is the "the boundary is the kernel" claim, sourced.
- [The lateral-movement view — NotPetya/Maersk reconstruction (Wired, 2018)](https://www.wired.com/story/notpetya-cyberattack-ukraine-russia-code-crashed-the-world/) (~20 min) — read the Maersk section for the *flat interior* failure that microsegmentation exists to prevent; it makes the stakes of the deny case concrete.

**Hands-on: kind + Cilium + Hubble setup (~1 hr)**
- [Getting Started with Cilium on kind (Cilium docs)](https://docs.cilium.io/en/stable/installation/kind/) (~25 min) — the exact bootstrap the lab uses; read once before `make up` so you know what the install is doing.
- [Observing network flows with Hubble (Cilium docs)](https://docs.cilium.io/en/stable/observability/hubble/setup/) (~20 min) — how to enable Hubble and read a drop verdict with its source/destination/label context; this is the audit trail your deliverable cites and the telemetry module 09 reuses.

## Key concepts
- Microsegmentation flips the default from allow-all to **deny-all, allow the minimum** — and the policy lives as code, not hand-maintained firewall rules. The policy *is* the perimeter.
- Cilium enforces in the **kernel via eBPF**, on the sending node, before the packet leaves the pod — so there's no "go around the boundary," even for a same-node pod.
- Rules are **label-scoped (`fromEndpoints`), not IP-scoped** — stable across pod restarts; but a bare app-label allow matches that label in *any* namespace, so bind app **and** namespace.
- **Default-deny silently breaks DNS** — allow port 53 to kube-system as part of the baseline or name resolution fails in ways that look like app bugs.
- **Prove both halves and try to pivot:** allow (backend→db) succeeds, deny (frontend→db) drops, and the deny holds under an active bypass attempt.
- Hubble / `cilium monitor` give per-flow drop verdicts with pod/namespace/label metadata — the same telemetry module 09 detects on.

## AI acceleration

A model will generate a `CiliumNetworkPolicy` from a plain-English intent in seconds — "backend pods reach database pods on port 80, deny everything else" — and that speed is exactly the risk, because **AI-generated network policy skews open in two predictable ways**: it forgets the DNS allow (so you'll think the policy is broken when it's actually working) and it writes the allow as a bare app-label match with no namespace constraint (so any namespace's `app: backend` pod inherits the allow). The posture holds — AI authors → you review every line → you own it — and here it has a concrete shape: never accept the policy on the allow path alone. Test the **deny** yourself, then *try to pivot around it*. That review is what the lab's required `verify-policy.sh` makes permanent: the secondary Judgment-as-Code beat is encoding your verdict ("frontend→db stays closed; backend→db stays open") as a script so a future edit that re-flattens the network turns the check red instead of going unnoticed.
