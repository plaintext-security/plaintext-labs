# Module 07 — Microsegmentation

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *shrink the blast radius to a single service boundary, not a VLAN.*

## Why this matters

A misconfigured firewall rule, a stolen service-account credential, or a container escape in one namespace can pivot to every other workload on the same flat internal network. Microsegmentation eliminates that flat surface: it enforces traffic policy at the workload level, so a compromised frontend pod cannot reach the database tier even if it is on the same host and the same Kubernetes cluster. The attacker gets one workload, not the blast radius of the whole east-west network.

In regulated environments — PCI-DSS, HIPAA, FedRAMP — microsegmentation is no longer optional. Auditors ask specifically how you isolate cardholder data or PHI workloads from other workloads in the same cluster. "We have a firewall at the edge" no longer satisfies scope.

## Objective

Deploy a Cilium-enforced network policy in a kind cluster that restricts database-tier access to backend pods only, confirm that frontend pods are denied, and trace the policy decision in Cilium's observability output.

## The core idea

Kubernetes provides a `NetworkPolicy` resource out of the box, but it requires a CNI plugin that actually enforces it — the default `kubenet` and `flannel` don't. Cilium is a CNI plugin built on eBPF that enforces network policy at the kernel level, which means the enforcement happens before a packet leaves the sending container, not at a perimeter firewall downstream. This is the architectural difference that matters: perimeter firewalls see only the traffic that escapes the cluster; Cilium sees — and can drop — traffic between pods on the same node.

eBPF enforcement has a practical consequence for attackers: there is no "bypass the policy by going around the network boundary" because the boundary is the kernel itself. A pod running on the same node as the database does not share a network path that bypasses the policy — it goes through the same eBPF hook. This is fundamentally different from a firewall rule that lives somewhere upstream.

The mental model for a Cilium `CiliumNetworkPolicy` is a **default-deny posture with explicit allows**. You annotate pods with labels (`app: backend`, `tier: database`), then write a policy that says "pods with label `tier: database` accept ingress only from pods with label `app: backend`." The policy is label-scoped, not IP-scoped — and that matters because pod IPs are ephemeral. IP-based rules break constantly in Kubernetes because pods restart with new IPs; label-based rules are stable because labels follow the workload.

A common gotcha is the interaction between default-deny and cluster-internal services like CoreDNS. A strict `default deny all` policy that forgets to allow DNS breaks name resolution for every pod, which breaks everything silently in ways that look like application bugs rather than network policy. Always start with an explicit allow for port 53 to kube-system DNS, or use Cilium's cluster entity selectors to permit DNS traffic.

The observability story is where Cilium separates from simpler CNI plugins. `cilium monitor` and Hubble (Cilium's UI) give you a per-flow audit trail: "frontend tried to connect to database:5432 at timestamp T, policy X denied it." This is the equivalent of firewall logs, but at the workload level and correlated with Kubernetes metadata (pod name, namespace, labels) — exactly the signal that module 09 will use for detection.

## Learn (~3 hrs)

**Kubernetes NetworkPolicy fundamentals (~45 min)**
- [Kubernetes Network Policies (official docs)](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — the canonical reference for the `NetworkPolicy` resource shape; read the "Behavior of to and from selectors" section carefully — it is the most common source of misconfiguration.
- [A visual guide to Kubernetes networking fundamentals (Tigera blog)](https://www.tigera.io/learn/guides/kubernetes-networking/) — diagrams of pod-to-pod vs. service traffic; useful background before you write your first policy.

**Cilium and eBPF (~1 hr)**
- [Cilium Concepts — Network Policy](https://docs.cilium.io/en/stable/security/policy/) — the authoritative reference for `CiliumNetworkPolicy` vs. standard `NetworkPolicy`; understand the `fromEndpoints` selector before the lab.

**Hands-on: kind + Cilium setup (~45 min)**
- [Getting Started with Cilium on kind (Cilium docs)](https://docs.cilium.io/en/stable/installation/kind/) — the exact setup the lab uses; read through once before running `make up` so you know what the bootstrap is doing.

**Microsegmentation in practice (~30 min)**

## Key concepts
- Cilium enforces policy with eBPF at the kernel level — not a perimeter firewall, enforcement on every node.
- Policies are label-scoped (`fromEndpoints`), not IP-scoped — stable across pod restarts.
- Default-deny posture: write explicit allow rules, everything else is dropped.
- Always allow DNS (port 53 to kube-system) or pod name resolution breaks silently.
- `cilium monitor` and Hubble provide per-flow audit logs correlated with Kubernetes metadata.
- Microsegmentation satisfies PCI-DSS/HIPAA workload isolation requirements that perimeter firewalls cannot.

## AI acceleration

AI can generate `CiliumNetworkPolicy` YAML from a description of your intent — tell it the namespaces, the label selectors, and the traffic direction you want to allow. What you must test yourself: the **deny case**. A policy that only allows `backend → database` must also be verified to deny `frontend → database`. AI drafts the YAML; you run `kubectl exec` to confirm both paths and check `cilium monitor` output to see the drop event.
