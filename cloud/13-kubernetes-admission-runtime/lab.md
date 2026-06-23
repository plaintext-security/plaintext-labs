# Lab 13 — Encode the Bouncer: Admission Policy as Code, Then a Camera for the Gap

*Variant D · breach-driven, build-first. [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs on a local
[`kind`](https://kind.sigs.k8s.io/) cluster — no cloud account required.

**Prerequisites:** Docker (running), `kind` >= v0.23.0, `kubectl`, and `helm`.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/13-kubernetes-admission-runtime
make up        # create kind cluster, install Kyverno + Falco (Helm), apply seed policies
make demo      # non-compliant pod (denied) + compliant pod (admitted); fire a Falco alert
make shell     # kubectl shell into the cluster to work
make down      # delete the cluster when done
```

**What this lab is — and isn't (read this).** This one *does* enforce: Kyverno installs in `Enforce`
mode, so a denied pod genuinely bounces at the API server — `kubectl apply` returns the error, the pod
never starts. That's the point of admission control and you'll see it for real. The seed gives you two
policies and leaves you to write the rest; the lab is the *building*, not a tour. Falco runs as a
DaemonSet on the node and watches real syscalls.

> This lab runs on a local kind cluster you own. Only test clusters you own or have explicit written
> permission to access. The "attacks" here are `kubectl exec` into your own pods.

## Scenario
The target account is rolling out Kyverno to its EKS clusters after reading the Graboid write-up in a
threat brief: *a worm spread because exposed container endpoints would run anything handed to them.*
You're the security engineer who owns the initial policy set. Your job: encode the verdict "these pod
specs should never be admitted" as Kyverno policy that *holds for every future pod*, prove it blocks the
bad and admits the good, then add one Falco rule for the behavior a manifest can't reveal — because
prevention without detection is blind to its own gaps.

## Do

### Part 1 — Read the door that exists, then prove it works

1. [ ] **List what's already guarding the door.** `kubectl get clusterpolicies`. For each, note its
   `validationFailureAction` (`Audit` or `Enforce`) and what it checks. Read
   `manifests/policies/disallow-privileged.yaml` and `require-non-root.yaml`: find the `deny` condition
   and the **exact spec path** it inspects (e.g. `containers[].securityContext.privileged`). The path is
   the policy — get it wrong and the policy admits the bad pod while looking right.

2. [ ] **Watch the bouncer reject.** `kubectl apply -f manifests/pod-bad.yaml` — it should be **denied**
   at the API server. Copy the exact error. Which policy fired, and on which field? Then
   `kubectl apply -f manifests/pod-good.yaml` and confirm it reaches `Running`
   (`kubectl get pod lab-compliant`). You've now seen prevention happen *before* a container started —
   the moment Graboid never met.

### Part 2 — Encode the verdicts you called

Your README prediction said all four pod specs should never be admitted. The seed covers two
(`privileged`, root). **Write the other two as policy** — this is the judgment-as-code build.

3. [ ] **`disallow-host-path` — block the node-filesystem mount.** Write a `ClusterPolicy` that denies any
   pod with a `hostPath` volume (`hostPath: /` is how you read `/etc/shadow` from a "contained" pod).
   *Hint: a `deny` rule over `request.object.spec.volumes[]` checking for the `hostPath` key.* Apply it,
   then prove it: a pod mounting `hostPath: { path: "/" }` is denied; a pod with only an `emptyDir` is
   admitted.

4. [ ] **`disallow-host-namespaces` — block the namespace escape.** Write a `ClusterPolicy` that denies
   `hostNetwork: true`, `hostPID: true`, or `hostIPC: true` at the pod level. Prove it: a pod setting any
   of the three is denied; a pod setting none is admitted.

5. [ ] **Run the rollout the right way (the operational lesson).** Set *one* of your new policies to
   `Audit`, apply a violating pod, and read `kubectl get policyreport -A` — the violation is logged but
   the pod runs. Now flip it to `Enforce` and re-apply: now it's blocked. Write down why a real cluster
   starts every policy in `Audit`. This ordering is the difference between a clean rollout and a 2 AM
   page.

### Part 3 — A camera for the gap the door can't close

6. [ ] **Admit a compliant pod, then misbehave inside it.** Tail Falco in a second terminal
   (`make logs-falco`). The pod passed every admission policy — now do the thing the manifest never
   revealed: `kubectl exec lab-compliant -- sh -c 'cat /etc/shadow 2>/dev/null || cat /etc/passwd'`.
   Note which rule fires and its priority. **Ask yourself: could *any* Kyverno policy have prevented
   this?** (No — the spec was compliant; the *behavior* is the signal. That is the gap.)

7. [ ] **Write the runtime rule for the gap.** Graboid's heirs land via a foothold and then `exec` to
   pivot. Author one Falco rule (in `manifests/falco-runtime-rules.yaml`) that fires on **a process
   executing from `/tmp`** inside a container — `kubectl exec lab-compliant -- sh -c 'cp /bin/sh /tmp/sh
   && /tmp/sh -c id'`. *Hint: condition on `evt.type=execve` and `proc.exepath` under `/tmp`; set a clear
   `output` with `%k8s.pod.name` and a `priority`.* Reload Falco, re-run the exec, confirm **your** rule
   fires — and that a benign in-container process does *not* (reduce the false positive). A rule that
   fires on everything is noise nobody reads.

## Success criteria — you're done when
- [ ] `kubectl apply -f pod-bad.yaml` is denied with a Kyverno error quoting the policy and field; `pod-good.yaml` reaches `Running`.
- [ ] Your `disallow-host-path` and `disallow-host-namespaces` policies each **deny** a violating pod and **admit** a compliant one — verified, not assumed.
- [ ] You demonstrated the `Audit` → `Enforce` flip on one policy and can say in one sentence why production starts in `Audit`.
- [ ] Your custom Falco rule fires on the `/tmp` execution with pod context and does **not** fire on a benign process.
- [ ] You can answer in writing: *which of the Part-3 actions could admission policy have prevented, and why is the answer "none"?*

## Deliverables
- `manifests/policies/disallow-host-path.yaml` and `disallow-host-namespaces.yaml` — your two new admission policies (the prevention-as-code).
- `manifests/falco-runtime-rules.yaml` — with your `/tmp`-execution rule added (the detection for the gap).
- `policy-report.md` — admit/deny results with the exact Kyverno errors, the `Audit`→`Enforce` note, your Falco alert text, and the layered-model answer.

Commit these four. Cluster state, kubeconfigs, and secret values stay out of the commit.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your four "never admit" verdicts only hold if a
policy *proves* them on every change, not just when you remember to apply it. Write a CI gate
(`validate-policies.yaml`, a GitHub Actions workflow) that runs the **`kyverno` CLI** (`kyverno apply`)
to dry-run *all* your policies against the manifests in the repo — **no live cluster** — and **fails the
build** when `pod-bad.yaml` (or a host-path / host-namespace pod) is admitted, and **passes** when
`pod-good.yaml` is. Have a model draft the workflow; **read every line** and confirm three things: it
runs `kyverno apply`, not `kubectl apply`; it fails on a denied manifest for the *right* policy; and it
succeeds on the compliant one. This is the bouncer encoded so a bad pod can't merge to the cluster
config in the first place — your verdict, made un-recurrable, exactly the gate the capstone reuses.

## AI acceleration
Paste a pod spec and ask a model which of your policies deny it and what the minimal `securityContext`
fix is — reliable on field-reading, and a good first-draft policy author. But it cannot tell you the
policy's *mode* (`kubectl get clusterpolicy`), and it will happily write a `deny` whose path is wrong so
the policy silently admits the bad pod. Prove every policy against the bad *and* the good manifest with
`make demo` before you trust it — a policy that doesn't block is worse than none. Same discipline for the
Falco rule: the model drafts the `condition`; you confirm it fires on the exec and stays quiet otherwise.

## Connects forward
- The policies here are what module 14's `stratus-red-team` / Kubernetes attacks try to bypass — your door is the thing the purple-team probes.
- Falco's structured JSON output becomes the detection signal that module 15 ingests into a SIEM and correlates; module 16 reconstructs an incident from it.
- The `kyverno apply` CI gate is a direct sibling of the IaC gate from module 06 and the RBAC/NetworkPolicy-as-code from module 12 — all converge in the **capstone**, where a green pipeline rebuilds the *hardened* cluster and the gate fails the *original* permissive config.

## Marketable proof
> "I write Kubernetes admission policy as code — denying privileged, host-mount, host-namespace, and
> root pods at the API server before they start — roll it out `Audit`→`Enforce` the safe way, gate it in
> CI with the Kyverno CLI, and layer a tuned Falco rule for the runtime behavior admission can't see. I
> can explain why prevention without detection is blind to its own gaps."

## Stretch
- Add a Kyverno **mutate** policy that auto-injects `runAsNonRoot: true` and `allowPrivilegeEscalation: false` into any pod missing them, and confirm `kubectl describe pod` shows the mutated values — defense that doesn't depend on the developer.
- Write a Kyverno **generate** policy that drops a default-deny NetworkPolicy into every new namespace (the module-12 control, applied automatically) — closing the lateral-movement path Graboid used to hop hosts.
- Wire Falco output to a webhook (a local HTTP listener or `ngrok`) so the `/tmp`-exec alert lands somewhere a responder would actually see it.
