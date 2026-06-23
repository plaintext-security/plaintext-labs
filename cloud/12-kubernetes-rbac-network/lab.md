# Lab 12 — Ship It Like Tesla, Then Cut It: RBAC & Network Policy as Code

*Variant D · build-first / audit→build. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs on a local
[`kind`](https://kind.sigs.k8s.io/) cluster you own — no cloud account, no real credentials.

**Prerequisites:** Docker (running), `kind` (≥ v0.23.0), and `kubectl`.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/12-kubernetes-rbac-network
make up         # create the kind cluster + apply the seeded misconfigured RBAC (ships it "like Tesla")
make demo       # run kube-bench + show the cluster-admin SA findings
make shell      # drop a kubectl shell into a pod running as the over-privileged SA
make down       # delete the cluster when done
```

The seeded cluster (single-node, Kubernetes v1.30) is deliberately shipped wrong: a `ci-deployer`
ServiceAccount bound to **`cluster-admin`**, a `demo-pod` that mounts its token, a `payments` namespace
with **no NetworkPolicy** (flat network), and a `kube-bench` job. The `manifests/` dir has both the broken
and the fixed RBAC/NetworkPolicy so you can diff your work against a reference — try it yourself first.

> **Authorization.** This lab runs against a local `kind` cluster you own. The exploitation steps
> (reading every Secret, creating a privileged pod) are intentional and self-contained. Only test
> clusters you own or have explicit written permission to access — never run these against a shared or
> production cluster.

**Honest about the lab.** The seeded Secrets are the cluster's own (`kube-system` bootstrap tokens, CA,
controller creds) plus a planted lab Secret standing in for "the AWS keys in a pod" — this lab does **not**
reach a real cloud account. The skill is identical: a `cluster-admin` SA reads Secrets it shouldn't, and
in the real Tesla incident those Secrets were AWS credentials. You rebuild the *mechanism*, then close it.

## Scenario
The target account provisioned an EKS-style cluster six months ago. A contractor gave the CI/CD pipeline's
ServiceAccount `cluster-admin` "to get things working," and the `payments` namespace has no segmentation —
exactly the two conditions that, on a Tesla cluster in 2018, turned an open dashboard into stolen cloud
keys and a cryptojacking bill. A security review just flagged it and handed it to you. **Build the fix:**
least-privilege RBAC and a default-deny-plus-allow NetworkPolicy, both as code, both verified.

## Do

### Phase 1 — Audit: see what shipped (the Tesla conditions)

1. [ ] **Run the benchmark.** `make demo` — read the kube-bench output. How many FAILs in **section 5
   (RBAC and Service Accounts)**? Note the control ID and remediation text for the `cluster-admin` /
   over-broad-binding finding. This is the audit a platform team runs on every new cluster.

2. [ ] **Prove the RBAC blast radius — the prediction from the README.** `make shell` drops you into
   `demo-pod`, running as `ci-deployer`. You predicted what a compromised pod can reach; now prove it:
   - `kubectl auth can-i --list` — note this SA can do *everything*.
   - `kubectl get secrets -n kube-system` — read Secrets across namespaces, including the planted
     `cloud-creds` Secret. **This is the Tesla hop:** a workload SA reading credentials it should never see.
   - `kubectl run pwned --image=alpine --privileged=true --restart=Never -- sleep 3600` then
     `kubectl get pod pwned` — the SA can launch a privileged pod (a node-escape primitive). Clean up:
     `kubectl delete pod pwned`.

3. [ ] **Prove the network is flat.** From a pod in `default`, reach the `payments-api` Service in the
   `payments` namespace (the lab seeds a probe; or
   `kubectl run probe --rm -it --image=curlimages/curl --restart=Never -- curl -s payments-api.payments:8080`).
   It responds. **Record:** with no NetworkPolicy, an unrelated namespace reaches payments — the flat LAN.

### Phase 2 — Build: author the cut and re-verify

4. [ ] **Cut the RBAC to the minimum.** Read `manifests/rbac-bad.yaml` (the `cluster-admin`
   ClusterRoleBinding) and write the replacement in `manifests/rbac-fixed.yaml` — a **namespace-scoped
   Role** granting only the verbs the CI pipeline needs (`get/list/create/update/patch` on
   `deployments`, `services`, `configmaps`; `get/list` on `pods` — no Secrets, no cluster scope), bound
   with a **RoleBinding**, and set `automountServiceAccountToken: false`. A reference solution is bundled —
   write yours first, then diff.

5. [ ] **Apply and re-verify the RBAC cut.**
   `kubectl delete -f manifests/rbac-bad.yaml && kubectl apply -f manifests/rbac-fixed.yaml`. Re-run from
   `demo-pod`: `kubectl auth can-i get secrets -n kube-system` must now return **no**, and
   `kubectl auth can-i --list` must show only the scoped deploy verbs. The cut is real only when the
   dangerous action is denied *and* the legitimate one (`create deployments` in `default`) still works.

6. [ ] **Default-deny the network, then add back the one flow.** Apply
   `manifests/netpol-default-deny.yaml` (`podSelector: {}`, ingress, no rules) to `payments`. Re-run the
   probe from step 3 — it must now **fail** (denied). Then apply `manifests/netpol-allow-frontend.yaml`,
   which permits ingress on the app port **only from pods labelled `app=frontend`** in `default`. Verify:
   a `frontend`-labelled pod reaches `payments-api`; an unlabelled pod does not. This is the firewall
   default-deny from module 04, expressed in the pod plane.

7. [ ] **Re-audit.** Re-run kube-bench (or `make demo`) and confirm the section-5 RBAC finding has
   cleared on the fixed binding. The before/after kube-bench delta goes in your report.

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
