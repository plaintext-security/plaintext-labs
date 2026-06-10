# Module 13 — Kubernetes — Admission & Runtime

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *policy-as-code: the control you apply before a workload starts is worth ten detections after it does.*

## Why this matters
Detection without prevention is surveillance. Module 11 showed that Falco can detect a privileged container escape *after it happens*; module 12 showed that kube-bench finds RBAC misconfigurations *after they're deployed*. The gap is admission: the moment a pod spec is submitted to the API server, before any container starts, is the last cheap moment to enforce policy. Kyverno, Open Policy Agent/Gatekeeper, and the built-in Pod Security Admission controller are the tools that close this gap — they evaluate policy against the manifest itself and return an allow or deny before the scheduler ever sees the pod. Financial services teams facing PCI DSS and SOC 2 Type II use admission policies to enforce that no production workload can start with `privileged: true`, no root containers, and no images from unscanned registries — centrally, without relying on every developer to remember.

## Objective
Deploy Kyverno to a kind cluster, write and apply policies that block privileged pods and require non-root users, demonstrate a compliant and a non-compliant deployment, and integrate Falco to detect runtime violations that bypass or follow policy.

## The core idea
The Kubernetes API server runs an admission webhook chain: every `CREATE` or `UPDATE` for a pod passes through registered webhooks before it is persisted and scheduled. An admission controller can *mutate* the manifest (defaulting fields) or *validate* it (allowing or rejecting). Kyverno registers itself as both. A Kyverno ClusterPolicy is a declarative YAML document that specifies a pattern the manifest must match — or must not match — and an action: `Audit` (log violations, let the pod start) or `Enforce` (deny the API call with a human-readable error). The policy lives in git, is applied with `kubectl apply`, and is version-controlled alongside the cluster configuration. This is policy-as-code.

The critical operational distinction is `Audit` vs. `Enforce` mode. Teams deploying Kyverno to an existing cluster invariably start in `Audit` mode: log every violation without blocking, collect a few weeks of data to understand how many existing workloads would fail, then flip individual policies to `Enforce` as the workloads are remediated. Jumping straight to `Enforce` in a production cluster is how teams page at 2 AM because a CronJob couldn't start. The workflow is: `Audit` → understand violations → fix workloads → `Enforce`. Kyverno's Policy Report CRD surfaces audit violations as Kubernetes objects queryable with `kubectl get policyreport`.

Runtime security via Falco complements admission policy, it does not replace it. Admission policy catches what a manifest says before it starts; runtime detection catches what a process does after it starts. A policy bypass (an image that slipped through before the policy was in place), a living-off-the-land technique (legitimate binaries doing malicious things), and a post-exploitation action (reading a credential file, opening a reverse shell) are all invisible to admission policy. The layered model is: admission prevents known-bad configuration → runtime detects known-bad behaviour → SIEM correlates the signal. Each layer has a different false-positive profile and a different response latency.

For Meridian Financial's engineering team, the practical win of Kyverno is *shifting left without changing developers' workflows*. Developers submit `kubectl apply` normally; the admission webhook returns a human-readable error explaining what policy was violated and what to change. The alternative — a code review comment asking someone to add `securityContext.runAsNonRoot: true` — is slower, error-prone, and doesn't scale. Policy-as-code makes security requirements executable and reviewable. The Kyverno policy for "no privileged containers" is ten lines of YAML that the security team owns, not a checklist item that the developer team has to remember.

## Learn (~3 hrs)

**Kubernetes admission control (~1 hr)**
- [Kubernetes docs — Admission Controllers Reference](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) — read the introduction and the "Why do I need admission controllers?" section; it explains the validation webhook chain that Kyverno and OPA plug into.
- [Kubernetes docs — Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) — the built-in admission controller for Pod Security Standards; understand the `baseline` and `restricted` profiles and how they relate to Kyverno policies.

**Kyverno (~1 hr)**
- [Kyverno documentation — Writing Policies](https://kyverno.io/policies/) — the primary reference; read the "Validate", "Mutate", and "Policy Reports" sections. This is the vocabulary for writing the lab policies.
- [Kyverno policy library](https://kyverno.io/policies/) — a browsable library of community policies; look at the "Disallow Privileged Containers" and "Require Run As Non-Root" policies — they are the starting point for the lab.

**Falco at the cluster level (~1 hr)**
- [Falco documentation — Kubernetes deployment](https://falco.org/docs/install-operate/deployment/#kubernetes) — how Falco integrates with Kubernetes; the DaemonSet deployment model and how alerts include Kubernetes metadata.
- [Sysdig blog — "Falco for Kubernetes security: a practical guide"](https://falco.org/docs/getting-started/) — a practitioner walkthrough of Falco in a real Kubernetes context; runtime rules, output channels, and the gap that admission control doesn't cover.

## Key concepts
- Admission webhooks: the API server's last checkpoint before a resource is persisted
- Kyverno ClusterPolicy: `Validate` (allow/deny) vs. `Mutate` (default/transform)
- `Audit` vs. `Enforce` mode — the production rollout pattern
- Policy Reports: Kyverno's violation log as Kubernetes objects
- Admission policy ≠ runtime security: configuration vs. behaviour
- Pod Security Standards: `privileged`, `baseline`, `restricted` profiles
- MITRE ATT&CK T1610 (Deploy Container), T1611 (Escape to Host), T1525 (Implant Internal Image)

## AI acceleration
Paste a pod spec that a developer submitted into a model and ask it to identify which Kyverno policies from the library would deny it, and what changes the developer needs to make. It's reliable at reading `securityContext` fields and matching them against known policy patterns. What it cannot do is tell you whether the policy is configured in `Audit` or `Enforce` mode in your cluster — that requires `kubectl get clusterpolicy`. Use the model to draft the Kyverno policy YAML and the compliant pod spec; you apply both and verify the expected allow/deny outcome with `make demo` before treating the policy as production-ready.
