# Lab 13 — Kyverno Admission Policies and Falco Runtime Detection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

**Prerequisites:** Docker (running), `kind` >= v0.23.0, `kubectl`, and `helm` installed.

```bash
# Install helm (if not present)
# macOS:  brew install helm
# Linux:  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version   # should print v3.x.x
```

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/13-kubernetes-admission-runtime
make up        # create kind cluster, install Kyverno + Falco via Helm, apply seed policies
make demo      # try a non-compliant pod (denied) and a compliant pod (allowed); show Falco alert
make shell     # kubectl shell in the cluster for exploration
make down      # delete the kind cluster
```

The environment provides:
- A `kind` cluster (`plaintext-lab-13`) with Kubernetes v1.30
- Kyverno installed via Helm (v3.2.x) in `Enforce` mode
- Two seed policies: `disallow-privileged.yaml` and `require-non-root.yaml`
- A Falco DaemonSet monitoring the node
- `manifests/pod-bad.yaml` — a non-compliant pod that violates both policies
- `manifests/pod-good.yaml` — a compliant pod that should be admitted

> This lab runs on a local kind cluster you own. Only test clusters you own or have explicit written permission to access.

## Scenario
Meridian Financial is rolling out Kyverno to their EKS cluster to enforce container security posture. You are the security engineer responsible for writing the initial policy set, testing it, and documenting the admit/deny decisions. You also need to show that Falco catches a runtime violation that occurs after a compliant pod is admitted — because policy and runtime are complementary, not redundant.

## Do

**Phase 1 — Explore the seeded Kyverno policies**

1. [ ] `kubectl get clusterpolicies` — list the installed policies.
   For each policy, note the `validationFailureAction` (`Audit` or `Enforce`) and what it checks.

2. [ ] Read `manifests/policies/disallow-privileged.yaml`.
   What is the `deny` condition? What exact field in the pod spec does it check, and at what
   path within the container's `securityContext`?

3. [ ] Read `manifests/policies/require-non-root.yaml`.
   This policy requires `runAsNonRoot: true` OR `runAsUser > 0`. Why is this check paired — what does `runAsNonRoot: true` alone miss?

**Phase 2 — Test the policies**

4. [ ] Try to deploy the non-compliant pod:
   `kubectl apply -f manifests/pod-bad.yaml`
   The API server should return a denial. Copy the exact error message into your notes.
   Which policy fired, and what field triggered it?

5. [ ] Deploy the compliant pod:
   `kubectl apply -f manifests/pod-good.yaml`
   Confirm it enters `Running` state: `kubectl get pod lab-compliant`

6. [ ] `kubectl get policyreport -A` — Kyverno writes audit results as Kubernetes objects.
   How many `fail` results are recorded? Open one: `kubectl describe policyreport -n default`

**Phase 3 — Write and apply a new policy**

7. [ ] Write a new Kyverno `ClusterPolicy` called `disallow-latest-tag` that denies any pod
   using an image with `:latest` or no tag (e.g. `nginx` or `nginx:latest`).
   *Hint: use a `deny` condition with `image.tag` check or a `pattern` match on the image field.
   See the [Kyverno Policy Library](https://kyverno.io/policies/) for policy examples and best practices.*

8. [ ] Apply your policy: `kubectl apply -f disallow-latest-tag.yaml`

9. [ ] Test it: `kubectl run tag-test --image=nginx` (should be denied).
   Then: `kubectl run tag-test --image=nginx:1.27` (should be allowed).

**Phase 4 — Falco runtime detection**

10. [ ] In a separate terminal: `make logs-falco` to tail Falco output.

11. [ ] From inside `lab-compliant` pod, trigger a suspicious action:
    `kubectl exec lab-compliant -- sh -c 'cat /etc/shadow 2>/dev/null || cat /etc/passwd'`
    Check the Falco log — does a rule fire? Note the rule name and priority.

12. [ ] Now write a `/tmp` execution attempt:
    `kubectl exec lab-compliant -- sh -c 'cp /bin/sh /tmp/sh && /tmp/sh -c id'`
    Does Falco detect the execution from `/tmp`? Why is execution from `/tmp` a suspicious signal?

13. [ ] **Reflect on the layered model:** Could the Kyverno admission policy have prevented
    steps 11 and 12? Why or why not? When does runtime detection provide value that admission policy cannot?

## Success criteria — you're done when
- [ ] `kubectl apply -f pod-bad.yaml` is denied with a Kyverno error message quoting the policy name.
- [ ] `kubectl apply -f pod-good.yaml` creates a Running pod.
- [ ] Your `disallow-latest-tag` policy denies `nginx` and allows `nginx:1.27`.
- [ ] You have a Falco alert from the runtime step, with the rule name and container context.
- [ ] You have written down the answer to the layered model question (step 13).

## Deliverables
- `policy-report.md` — the admit/deny results, Kyverno error messages, Falco alert text, and your layered model answer.
- `manifests/policies/disallow-latest-tag.yaml` — your new Kyverno ClusterPolicy.
- `manifests/pod-good.yaml` — the compliant pod spec you verified.

Commit these three files. Cluster state, kubeconfigs, and secret values stay out of the commit.

## Automate & own it
**Required.** Write a GitHub Actions workflow `validate-policies.yaml` that uses `kyverno` CLI (`kyverno apply`) to dry-run your policies against the pod manifests in the repo, without a live cluster. Have a model draft the workflow; **you read every line** and verify: (1) it actually runs `kyverno apply` not just `kubectl apply`, (2) it fails on a denied manifest, and (3) it succeeds on the compliant one. Commit the workflow so policy violations block PRs before they ever reach a cluster.

## AI acceleration
Paste a pod spec into a model and ask it to identify which Kyverno policies from the library would deny it and what the minimal `securityContext` changes are to make it compliant. It's reliable at reading `securityContext` fields. Verify each suggested change actually passes the policy with `make demo` — the model doesn't know your policy's exact condition syntax.

## Connects forward
- Module 14 (Cloud Attack Techniques) uses these same cluster configurations as the target environment for simulated attacks with `stratus-red-team` — the policies you set here are what attackers try to bypass.
- Module 15 (Cloud Logging & Detection) ingests Falco's structured JSON output into a SIEM and writes correlation rules — the Falco alerts from this module become the detection signal.

## Marketable proof
> "I write Kyverno policy-as-code to enforce Kubernetes security posture at admission — blocking privileged containers, requiring non-root, and gating on image hygiene — and I layer Falco runtime detection to catch what policy alone can't prevent."

## Stretch
- Enable Kyverno `Mutation`: write a policy that *automatically adds* `runAsNonRoot: true` and `allowPrivilegeEscalation: false` to any pod that doesn't already set them. Test it: apply a pod without `securityContext` and confirm `kubectl describe pod` shows the mutated values.
- Write a Kyverno `generate` policy that automatically creates a default-deny NetworkPolicy for every new namespace.
- Configure Falco to output alerts to a webhook (use a simple `ngrok` or local HTTP listener) and trigger an alert from `make demo`.
