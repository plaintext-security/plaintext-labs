# Lab 12 — Kubernetes RBAC Audit and Network Policy

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

**Prerequisites:** Docker (running) and `kind` and `kubectl` installed.

```bash
# Install kind (if not present)
# macOS:  brew install kind
# Linux:  curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64 && chmod +x ./kind && mv ./kind /usr/local/bin/
kind version   # should print v0.23.0 or later

# Install kubectl (if not present)
# macOS:  brew install kubectl
# Linux:  curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && chmod +x kubectl && mv kubectl /usr/local/bin/
kubectl version --client
```

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/12-kubernetes-rbac-network
make up        # create the kind cluster and apply the seeded misconfigured RBAC manifests
make demo      # run kube-bench and show the misconfigured SA findings
make shell     # drop a kubectl shell into a pod using the over-privileged SA
make down      # delete the kind cluster
```

The environment provides:
- A `kind` single-node cluster (`plaintext-lab`) with Kubernetes v1.30
- `kube-bench` job pre-configured to run against the kind control plane
- A seeded misconfigured `ClusterRoleBinding` that gives a `ci-deployer` ServiceAccount `cluster-admin`
- A `demo-pod` that mounts the `ci-deployer` SA token and can call the Kubernetes API
- NetworkPolicy manifests in `manifests/` — one broken (no default-deny) and one fixed

> This lab runs on a local kind cluster you own. Only test clusters you own or have explicit written permission to access.

## Scenario
Meridian Financial's DevOps team provisioned an EKS cluster six months ago. The CI/CD pipeline deploys to it using a ServiceAccount created by a contractor who gave it `cluster-admin` "to get things working." A recent security review flagged it. You are the auditor: find the misconfiguration, understand its blast radius, fix it, and verify the fix. You also need to add a network isolation policy for the `payments` namespace that currently has no segmentation.

## Do

**Phase 1 — kube-bench audit**

1. [ ] `make demo` — run kube-bench and read the output. 
   How many HIGH findings does kube-bench report? Which CIS control ID covers RBAC-related findings?
   *Hint: look for controls in section 5.1 — "RBAC and Service Accounts."*

2. [ ] Identify the specific kube-bench finding about `cluster-admin` bindings.
   Note the control ID and the remediation text.

**Phase 2 — Explore the misconfigured ServiceAccount**

3. [ ] `make shell` — this drops you into `demo-pod`, which runs as the `ci-deployer` SA.
   Run: `kubectl auth can-i --list`
   What does the output tell you about the SA's permissions?

4. [ ] From inside `demo-pod`, list all secrets in `kube-system`:
   `kubectl get secrets -n kube-system`
   You can see bootstrap tokens, CA certs, and controller credentials. This is the blast radius.

5. [ ] Still from inside `demo-pod`, prove you can create a privileged pod:
   `kubectl run pwned --image=alpine --privileged=true --restart=Never -- sleep 3600`
   Confirm it starts: `kubectl get pod pwned`
   *This is exactly what an attacker with access to the CI pipeline could do.*

6. [ ] Clean up the test pod: `kubectl delete pod pwned`

**Phase 3 — Fix the RBAC**

7. [ ] Read `manifests/rbac-bad.yaml`. Identify the `ClusterRoleBinding` that grants `cluster-admin`.

8. [ ] Read `manifests/rbac-fixed.yaml`. The fixed version uses a namespace-scoped `Role` with only the verbs needed for deployment. Review the change: what `verbs` and `resources` does the replacement Role grant?

9. [ ] Apply the fix:
   ```bash
   kubectl delete -f manifests/rbac-bad.yaml
   kubectl apply -f manifests/rbac-fixed.yaml
   ```

10. [ ] Re-enter `demo-pod` and run `kubectl auth can-i --list` again.
    Confirm that `get secrets -n kube-system` is now denied.

**Phase 4 — Network Policy**

11. [ ] Check the current state: `kubectl get networkpolicy -n payments`
    There are no policies. List all pods in `payments` and confirm a pod in `default` can reach them (the demo seeds a simple web server).

12. [ ] Apply `manifests/netpol-default-deny.yaml` — a default-deny-all ingress policy for `payments`.
    Confirm the policy is in place: `kubectl get networkpolicy -n payments`

13. [ ] Re-run the connectivity test — the `default` namespace pod should now be denied.

14. [ ] Apply `manifests/netpol-allow-frontend.yaml` — allows ingress on port 8080 only from pods labelled `app=frontend` in the `default` namespace.
    Confirm a `frontend`-labelled pod can reach port 8080, and an unlabelled pod cannot.

## Success criteria — you're done when
- [ ] kube-bench output shows you have read it and identified the RBAC-related High findings.
- [ ] `kubectl auth can-i --list` before the fix shows `cluster-admin` equivalent permissions.
- [ ] `kubectl auth can-i --list` after the fix shows only the scoped deployment verbs.
- [ ] The `payments` namespace has a default-deny NetworkPolicy plus a targeted allow for `frontend`.
- [ ] You have verified connectivity before (allowed) and after (denied then selectively allowed) the NetworkPolicy changes.

## Deliverables
- `rbac-audit.md` — kube-bench findings summary, the identified ClusterRoleBinding, blast-radius demonstration, and before/after permission comparison.
- `manifests/rbac-fixed.yaml` — your least-privilege Role + RoleBinding replacement.
- `manifests/netpol-default-deny.yaml` and `manifests/netpol-allow-frontend.yaml` — the NetworkPolicy manifests.

Commit these files. Cluster kubeconfigs, SA tokens, and secrets stay out of the commit.

## Automate & own it
**Required.** Write a script `rbac-audit.sh` that runs `kubectl get clusterrolebindings -o json` and pipes it through `jq` to list every binding that references the `cluster-admin` ClusterRole, with the subject name and type. Have a model draft it; **you read every line** and run it against the kind cluster to confirm it catches `ci-deployer`. Extend it to also flag ServiceAccounts with `automountServiceAccountToken: true` (the default) — those are tokens waiting to be stolen.

## AI acceleration
Paste your `kube-bench` JSON output (from `--output json`) into a model and ask it to triage the findings by exploitability given "a single-tenant EKS cluster with no multi-tenancy." It will re-rank the findings by practical impact vs. theoretical concern. Validate each ranking against the CIS Benchmark remediation text — some kube-bench findings are genuinely low-risk in specific configurations; others sound low but are high-impact in a CI/CD context.

## Connects forward
- Module 13 adds Kyverno admission policies that enforce the RBAC principle at deploy time — the policy that blocks a pod from requesting a `cluster-admin`-equivalent SA is the automated gate for what you manually fixed here.
- Module 15 (Cloud Logging & Detection) integrates Kubernetes audit logs — the API calls you made with the over-privileged SA would appear there and are exactly the kind of signal a SIEM rule would catch.

## Marketable proof
> "I audit Kubernetes RBAC with kube-bench, identify ServiceAccount overprivilege, fix it with least-privilege Role definitions, and implement NetworkPolicy default-deny segmentation — all as code in git."

## Stretch
- Use `kubectl-who-can` (a kubectl plugin) to enumerate all subjects that can `create pods` in any namespace — this is the blast-radius query for "who can escape to the node?"
- Write a kube-bench CI check: a GitHub Actions workflow that runs kube-bench after cluster creation and fails if any High RBAC finding is present.
- Add a `PSS` (Pod Security Standards) `baseline` policy to the `payments` namespace and confirm it blocks `privileged: true` pods.
