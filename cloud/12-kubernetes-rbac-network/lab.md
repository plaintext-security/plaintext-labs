# Lab 12 — Ship It Like Tesla, Then Cut It: RBAC & Network Policy as Code

*Variant D · build-first / audit→build. [← Back to the module concept](README.md)*

> **Hands-on lab.** Environment: `plaintext-labs/cloud/12-kubernetes-rbac-network` (runs on a local
> [`kind`](https://kind.sigs.k8s.io/) cluster you own — no cloud account, no real credentials).
> **Objective:** ship a cluster the way Tesla shipped it (a `cluster-admin` ServiceAccount, a flat pod
> network), prove the cost, then **author least-privilege RBAC and a default-deny NetworkPolicy as code
> and re-verify the cut.** Target: **~90 min**, one finish line.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **RBAC is cloud IAM one layer down: Subject → Binding → Role.** | You already wrote this evaluation for AWS in module 02 — just relabel it for the cluster. |
| 2 | **The binding sets the scope, not the Role.** | A `RoleBinding` grants in one namespace; a `ClusterRoleBinding` grants in every namespace — same rules, different reach. |
| 3 | **The SA token is auto-mounted into every pod.** | Unless `automountServiceAccountToken: false`, a compromised process always has *a* key to the API server. |
| 4 | **`cluster-admin` on a workload SA = read every Secret, every namespace.** | That is the Tesla path: an over-broad SA reading credentials it should never see. |
| 5 | **NetworkPolicy is opt-in — no policy means a flat network across namespaces.** | The default-allow LAN you'd never ship on-prem; a deny in one namespace covers only that namespace. |
| 6 | **Least-privilege + default-deny only count when *verified*.** | `kubectl auth can-i` is the RBAC test; a connectivity probe is the network test. YAML that "looks right" isn't proof. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [it's IAM, one layer down](README.md#the-model-its-iam-one-layer-down).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A pod is compromised via app RCE. **By default**, what can it reach on the network, and what can its
   ServiceAccount token read?
2. `cluster-admin` is the `Resource: "*"` of Kubernetes. Map each RBAC piece to its cloud-IAM equivalent:
   ServiceAccount, Role, RoleBinding.

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs on a local
`kind` cluster you own — no cloud account, no real credentials.

**Prerequisites:** Docker (running), `kind` (≥ v0.23.0), and `kubectl`.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/12-kubernetes-rbac-network
make up         # create the kind cluster + apply the seeded misconfigured RBAC ("like Tesla")
make demo       # run kube-bench + show the cluster-admin SA findings
make shell      # drop a kubectl shell into demo-pod (runs as the over-privileged ci-deployer SA)
make down       # delete the cluster when done   (make reset = down + up)
```

The seeded cluster (single-node kind, Kubernetes v1.30, NetworkPolicy-enforcing CNI) is deliberately
shipped wrong: a `ci-deployer` ServiceAccount bound to **`cluster-admin`** (`ci-deployer-admin`
ClusterRoleBinding), a `demo-pod` that mounts its token, a `payments` namespace with **no
NetworkPolicy** (flat network), and a `kube-bench` job. The `manifests/` dir carries both the broken and
the fixed RBAC/NetworkPolicy so you can diff your work against a reference — **try it yourself first.**

> **▸ On track if:** `make demo` prints kube-bench **FAILs in section 5 (RBAC and Service Accounts)**,
> the `ci-deployer-admin` ClusterRoleBinding YAML, an `auth can-i --list` for `ci-deployer` that shows
> `*` on `*` (it can do everything), and `No resources found` for `networkpolicy -n payments` — the
> misconfigured cluster is live.

> **Authorization.** This lab runs against a local `kind` cluster you own. The exploitation steps
> (reading every Secret, creating a privileged pod) are intentional and self-contained. Only test
> clusters you own or have explicit written permission to access — never run these against a shared or
> production cluster.

**Honest about the lab.** The seeded Secrets are the cluster's own (`kube-system` bootstrap tokens, CA,
controller creds) plus a planted lab Secret standing in for "the AWS keys in a pod" — this lab does
**not** reach a real cloud account. The skill is identical: a `cluster-admin` SA reads Secrets it
shouldn't, and in the real Tesla incident those Secrets were AWS credentials. You rebuild the
*mechanism*, then close it.

---

## Scenario

The target account provisioned an EKS-style cluster six months ago. A contractor gave the CI/CD
pipeline's ServiceAccount `cluster-admin` "to get things working," and the `payments` namespace has no
segmentation — exactly the two conditions that, on a Tesla cluster in 2018, turned an open dashboard into
stolen cloud keys and a cryptojacking bill. A security review just flagged it and handed it to you.
**Build the fix:** least-privilege RBAC and a default-deny-plus-allow NetworkPolicy, both as code, both
verified. Each step runs the same rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Step 1 — Audit: read what shipped (the Tesla conditions)

**Concept (30 sec):** Flight-card #6. A platform team audits every new cluster with kube-bench (CIS
Benchmark); section 5 covers RBAC and Service Accounts.

**Do it:** `make demo`. Read the kube-bench output; note the control ID and remediation text for the
`cluster-admin` / over-broad-binding finding.

> **▸ On track if:** section 5 shows **FAIL(s)** on the over-broad binding, and the demo prints the
> `ci-deployer-admin` ClusterRoleBinding with `roleRef: cluster-admin`. **Record:** the control ID + the
> remediation line — this is the audit baseline you'll clear at the end.

### Step 2 — Prove the RBAC blast radius (the heart of it)

**Concept (30 sec):** Flight-cards #3 and #4. You predicted what a compromised pod can reach in the
warm-up; now prove it. `make shell` drops you into `demo-pod`, running as `ci-deployer`.

**Predict, then do** — from inside the pod:
- `kubectl auth can-i --list` — note this SA can do **everything**.
- `kubectl get secrets -n kube-system` — read Secrets across namespaces, including the planted
  `cloud-creds` Secret. **This is the Tesla hop:** a workload SA reading credentials it should never see.
- `kubectl run pwned --image=alpine --privileged=true --restart=Never -- sleep 3600` then
  `kubectl get pod pwned` — the SA can launch a privileged pod (a node-escape primitive).
  Clean up: `kubectl delete pod pwned`.

> **▸ On track if:** `auth can-i --list` shows `*` verbs on `*` resources, `get secrets -n kube-system`
> **returns Secret contents** (incl. `cloud-creds`), and the privileged `pwned` pod schedules.
> **Record:** owner = customer; the SA reads Secrets it doesn't own → the cloud-creds path.

### Step 3 — Prove the network is flat

**Concept (30 sec):** Flight-card #5. With no NetworkPolicy, every pod reaches every pod across
namespaces — the flat LAN.

**Do it:** from a pod in `default`, reach the `payments-api` Service in the `payments` namespace:
```bash
kubectl run probe --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s payments-api.payments:8080
```

> **▸ On track if:** the probe **responds** with `Payments API — seed data` — an unrelated namespace
> reached `payments` with no policy in the way. **Record:** owner = customer; plane = network; the flat
> pod network is default-allow.

### Step 4 — Cut the RBAC to the minimum, then re-verify

**Concept (30 sec):** Flight-cards #1 and #2. Replace the `cluster-admin` ClusterRoleBinding with a
**namespace-scoped Role + RoleBinding** — only the verbs the CI pipeline needs — and disable the token
auto-mount.

**Do it:** read `manifests/rbac-bad.yaml`, write your replacement in `manifests/rbac-fixed.yaml`
(get/list/create/update/patch on `deployments`, `services`, `configmaps`; get/list on `pods`; **no
Secrets, no cluster scope**; `automountServiceAccountToken: false`) — write yours first, then diff
against the bundled reference. Apply and re-verify:
```bash
kubectl delete -f manifests/rbac-bad.yaml
kubectl apply  -f manifests/rbac-fixed.yaml
kubectl auth can-i get secrets -n kube-system --as=system:serviceaccount:default:ci-deployer
kubectl auth can-i create deployments -n default --as=system:serviceaccount:default:ci-deployer
```

> **▸ On track if:** the first `auth can-i` now returns **`no`** (the dangerous action is denied) **and**
> the second returns **`yes`** (the legitimate deploy verb still works). The cut is real only when the
> denied *and* the allowed answer both land as expected.

### Step 5 — Default-deny the network, then add back the one flow

**Concept (30 sec):** Flight-card #5. `podSelector: {}` with no `ingress:` rules is the firewall
default-deny from module 04, expressed in the pod plane; then you add back only what the app needs.

**Do it:** apply the default-deny, re-probe (from Step 3 — it must now **fail**), then apply the targeted
allow and prove the flip:
```bash
kubectl apply -f manifests/netpol-default-deny.yaml      # default-deny-ingress in payments
kubectl run probe --rm -it --image=curlimages/curl --restart=Never -- curl -s --max-time 5 payments-api.payments:8080
kubectl apply -f manifests/netpol-allow-frontend.yaml    # allow only app=frontend in default, :8080
kubectl run frontend --rm -it --labels app=frontend --image=curlimages/curl --restart=Never -- curl -s --max-time 5 payments-api.payments:8080
```

> **▸ On track if:** after default-deny the unlabelled `probe` **times out / is refused** (denied); after
> the allow, a pod labelled `app=frontend` **gets** `Payments API — seed data` while any unlabelled pod
> still fails. Connectivity flips: reachable → denied → selectively reachable.

### Step 6 — Re-audit

**Do it:** re-run kube-bench (`make demo`, or the job alone) and confirm the section-5 RBAC finding has
**cleared** on the fixed binding. The before/after delta goes in your report.

> **▸ On track if:** the section-5 finding that FAILed on `rbac-bad.yaml` in Step 1 is no longer present
> against `rbac-fixed.yaml`.

---

## Prove the control (your finish line)

Least-privilege RBAC **and** default-deny networking, each proven with an **allow + deny pair** — not a
YAML that merely looks right:

1. **RBAC.** `auth can-i get secrets -n kube-system --as=system:serviceaccount:default:ci-deployer`
   returns **`no`** (deny) while `auth can-i create deployments -n default --as=…ci-deployer` returns
   **`yes`** (allow). The dangerous action is gone; the job still works.
2. **Network.** From `payments`' perspective: an `app=frontend` pod **reaches** `payments-api` (allow)
   and any other pod is **denied** (deny), with the default-deny in place.

If either control only denies (breaks the app) or only allows (proves nothing), the cut isn't done.

---

## Recall check — close the doc, answer from memory (3 min)

1. Map ServiceAccount, Role, RoleBinding, and `cluster-admin` to their cloud-IAM equivalents.
2. A pod is compromised. By default, what can it reach on the network and what can its SA read — and
   which two settings take each away?
3. Why isn't a default-deny NetworkPolicy in one namespace enough, and what two tests verify the RBAC and
   network cuts?

---

## Success criteria — you're done when

- [ ] You demonstrated the over-broad SA reaching `kube-system` Secrets (incl. the planted `cloud-creds`)
  and creating a privileged pod — the Tesla blast radius, reproduced.
- [ ] `kubectl auth can-i get secrets -n kube-system --as=system:serviceaccount:default:ci-deployer`
  returns **yes** before your fix and **no** after, while the legitimate deploy verbs still return **yes**.
- [ ] The `payments` namespace has a default-deny ingress policy **plus** a targeted allow, and you proved
  connectivity flips: reachable → denied → selectively reachable.
- [ ] kube-bench's section-5 RBAC finding is present on `rbac-bad.yaml` and cleared on `rbac-fixed.yaml`.

## Deliverables

- `rbac-audit.md` — kube-bench before/after summary, the identified `cluster-admin` binding, the
  blast-radius demonstration (Secrets + privileged pod), and the before/after `auth can-i` comparison.
- `manifests/rbac-fixed.yaml` — your least-privilege Role + RoleBinding (the portfolio artifact).
- `manifests/netpol-default-deny.yaml` and `manifests/netpol-allow-frontend.yaml` — the segmentation policies.

Commit these. Kubeconfigs, SA tokens, and Secret contents stay out of the commit.

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your finding is "a workload SA must never have
`cluster-admin` or read Secrets it doesn't own." Encode that verdict as a **check that fails the bad state
and passes the fix**, so it can't recur silently:

- A `conftest`/OPA-Rego (or `kubectl get clusterrolebindings -o json | jq` + assertions) policy that
  **fails** any binding to `cluster-admin` for a ServiceAccount subject, **fails** a workload SA granted
  `secrets` `get/list`, and **flags** any SA without `automountServiceAccountToken: false` — and **passes**
  your `rbac-fixed.yaml`.
- Run it against both `rbac-bad.yaml` (exit non-zero) and `rbac-fixed.yaml` (exit zero) and show it flips.

Have a model draft the Rego/jq; **review every line** and confirm it fails the bad binding for the *right*
reason (the `cluster-admin` roleRef, not an unrelated field). This is the same guardrail discipline you
built for IAM in module 02 — your cut, made un-recurrable, and the seed of the admission policy you'll
write in module 13.

## Definition of done (`kubernetes-rbac-network` ✅)

- [ ] `make demo` reproduced the section-5 RBAC FAIL and the `cluster-admin` blast radius (Secrets + privileged pod).
- [ ] `rbac-fixed.yaml` is a namespace-scoped Role + RoleBinding with `automountServiceAccountToken: false`, written before diffing the reference.
- [ ] The RBAC allow+deny pair lands as expected (`get secrets` = no, `create deployments` = yes).
- [ ] `payments` has default-deny + targeted allow, and connectivity flips reachable → denied → selectively reachable.
- [ ] Your guardrail fails `rbac-bad.yaml` and passes `rbac-fixed.yaml`.
- [ ] You can explain all six flight-card facts cold.

## AI acceleration

Paste your kube-bench JSON (`--output json`) and ask a model to triage findings by exploitability for "a
single-tenant cluster, CI/CD has a real SA." It re-ranks theory vs. practical impact well. Then paste your
NetworkPolicy and ask it to find a path that still reaches `payments` — if it can (a forgotten namespace, a
missing egress rule, an unlabelled pod that matches), your policy is too narrow or your coverage is partial.
Validate every claim against the live cluster with `auth can-i` and the connectivity probe — the model
can't see cluster state.

## Connects forward

- **Module 13 (Admission & Runtime)** turns this manual fix into a *gate*: a Kyverno admission policy that
  blocks a pod from requesting a `cluster-admin`-equivalent SA at deploy time, and Falco for what slips past
  at runtime — the automated enforcement of what you fixed by hand here.
- **Module 04 (Cloud Network Security)** is the same default-deny you wrote there for Security Groups, now
  in the pod plane — the SG ruleset and the NetworkPolicy are one discipline in two layers.
- **Module 15 (Logging & Detection)** ingests Kubernetes audit logs: the `get secrets` and
  `create pod --privileged` calls you made are exactly the signals a detection rule fires on.

## Marketable proof

> "I audit Kubernetes RBAC with kube-bench, reproduce the over-privileged-ServiceAccount blast radius
> (read cluster Secrets, launch a privileged pod), and close it with least-privilege Role/RoleBinding and
> default-deny NetworkPolicy — all as code in git, verified with `kubectl auth can-i` and connectivity
> probes, and guarded by a policy check that fails the over-broad binding in CI. I can explain why this is
> the same model that exposed Tesla's cloud keys in 2018."

## Stretch

- Add a `PodSecurity` `restricted` label to the `payments` namespace and confirm it blocks
  `privileged: true` pods (closing the node-escape primitive from step 2 at the namespace level).
- Use `kubectl-who-can create pods --all-namespaces` to enumerate every subject that can launch a pod —
  the blast-radius query for "who can escape to the node?"
- Extend your guardrail into a GitHub Actions workflow that runs kube-bench after cluster creation and
  fails the pipeline on any High section-5 RBAC finding.
