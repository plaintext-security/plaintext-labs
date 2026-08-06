# Lab 13 — Encode the Bouncer: Admission Policy as Code, Then a Camera for the Gap

> **Hands-on lab.** Environment: `plaintext-labs/cloud/13-kubernetes-admission-runtime` (runs on a local
> [`kind`](https://kind.sigs.k8s.io/) cluster — **no cloud account**). Objective: **encode the "never
> admit" verdict as Kyverno policy that blocks a bad pod at the API server, then add one Falco rule for
> the behavior admission can't see** — a preventive + detective pair. Target: **~2 hrs**, one finish line.
>
> *Variant D · breach-driven, build-first. [← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Admission is the bouncer; runtime is the camera. You need both.** | Each is blind to exactly what the other catches — the whole reason this is one module. |
| 2 | **The bouncer reads the *spec* before any container starts.** | A Kyverno `ClusterPolicy` denies at `kube-apiserver` — cheap prevention that runs once. |
| 3 | **Four specs must never be admitted.** | `privileged`, `hostPath: /`, `hostNetwork/hostPID`, and the silent default — **runAsRoot**. |
| 4 | **The path *is* the policy.** | A `deny` whose spec path is subtly wrong admits the bad pod while looking correct — prove every one. |
| 5 | **Roll out `Audit` → understand → `Enforce`.** | Jumping straight to `Enforce` on a live cluster is how a CronJob can't start at 2 AM. |
| 6 | **Falco fires on behavior the manifest never reveals.** | `exec` into a pod, a proc from `/tmp`, a sensitive-file read — the gap the door can't close. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [model: the bouncer and the camera](README.md#the-model-the-bouncer-and-the-camera), and the
> [Kyverno validate reference](https://kyverno.io/docs/policy-types/cluster-policy/validate/).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. You need **both** admission control and runtime detection. Name in one line what each one is *blind*
   to that the other catches.
2. Of the four "never admit" specs, which is the **most common** — and why is "nothing set at all"
   dangerous?

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs on a local `kind`
cluster; **Kyverno installs in `Enforce` mode**, so a denied pod genuinely bounces at the API server.

**Prerequisites:** Docker (running), `kind` >= v0.23.0, `kubectl`, and `helm`.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/13-kubernetes-admission-runtime
make up          # create kind cluster, install Kyverno + Falco (Helm), apply seed policies
make demo        # non-compliant pod (denied) + compliant pod (admitted); trigger a Falco alert
make shell       # ephemeral kubectl pod for cluster exploration
make logs-falco  # tail Falco output (run in a SECOND terminal)
make down        # delete the cluster when done   ·   make reset rebuilds from scratch
```

**What this lab is — and isn't.** This one *does* enforce: a denied pod really bounces at the API
server — `kubectl apply` returns the error and the pod never starts. The seed gives you **two** policies
(`disallow-privileged.yaml`, `require-non-root.yaml`) and leaves you to write the rest; the lab is the
*building*, not a tour. Falco runs as a DaemonSet on the node and watches **real** syscalls.

> **▸ On track if:** `make up` ends with `Cluster ready`, and `kubectl get clusterpolicies` lists
> `disallow-privileged-containers` and `require-run-as-non-root`, both with `ACTION` = `Enforce`.

> **Authorization note.** This lab runs on a local kind cluster you own. Only test clusters you own or
> have explicit written permission to access. The "attacks" here are `kubectl exec` into your own pods.

---

## Scenario

The target account is rolling out Kyverno to its EKS clusters after reading the Graboid write-up in a
threat brief: *a worm spread because exposed container endpoints would run anything handed to them* —
the same open door that let attackers cryptojack Tesla's own cluster. You're the security engineer who
owns the initial policy set. Your job: encode the verdict "these pod specs should never be admitted" as
Kyverno policy that *holds for every future pod*, prove it blocks the bad and admits the good, then add
one Falco rule for the behavior a manifest can't reveal — because prevention without detection is blind
to its own gaps. Each step runs the same rhythm: **Read → Do → Prove → Record.**

---

## Build it — read a little, do a little

### Step 1 — Read the door that exists, then watch it reject

**Concept (30 sec):** Flight-card #2 and #4. A `ClusterPolicy` is a spec pattern plus an action; the
**exact spec path** the `deny` inspects *is* the policy. Get the path wrong and it admits the bad pod
while looking right.

**Do it:** `kubectl get clusterpolicies`, then open `manifests/policies/disallow-privileged.yaml` and
`require-non-root.yaml` and find each `deny` condition and the spec path it checks (e.g.
`request.object.spec.containers[].securityContext.privileged`). Then make the bouncer reject:

```bash
kubectl apply -f manifests/pod-bad.yaml    # pod: lab-noncompliant — expect an ERROR
kubectl apply -f manifests/pod-good.yaml   # pod: lab-compliant — expect success
kubectl get pod lab-compliant
```

> **▸ On track if:** `pod-bad.yaml` is **denied** — the error names `disallow-privileged-containers`
> (and/or `require-run-as-non-root`) and quotes the failing field, and no `lab-noncompliant` pod exists.
> `lab-compliant` reaches `Running`. You've now seen prevention happen *before* a container started — the
> moment Graboid and Tesla never met. **Record** the exact error text.

### Step 2 — Encode the two verdicts you called (`hostPath`, host namespaces)

**Concept (30 sec):** Flight-card #3. The seed covers `privileged` and root; you predicted **all four**.
Write the other two — this is the judgment-as-code build.

**Do it:** author two new policies under `manifests/policies/`:

- **`disallow-host-path.yaml`** — deny any pod with a `hostPath` volume (`hostPath: /` is how you read
  `/etc/shadow` from a "contained" pod). *Hint: a `deny` over `request.object.spec.volumes[]` checking
  for the `hostPath` key.*
- **`disallow-host-namespaces.yaml`** — deny `hostNetwork: true`, `hostPID: true`, or `hostIPC: true` at
  the pod level.

Apply them (`kubectl apply -f manifests/policies/`) and prove each with a violating pod and a compliant
one (a pod with only an `emptyDir` / no host namespaces).

> **▸ On track if:** a pod mounting `hostPath: { path: "/" }` is **denied** by your `disallow-host-path`
> policy for the right field, and one with only `emptyDir` is **admitted**; a pod setting any of the
> three host namespaces is **denied**, and one setting none is **admitted** — verified, not assumed.
> **Record** which field each policy fired on.

### Step 3 — Run the rollout the right way (`Audit` → `Enforce`)

**Concept (30 sec):** Flight-card #5. `Audit` logs violations without blocking; you watch the reports,
remediate, *then* flip to `Enforce`.

**Do it:** set *one* of your new policies to `validationFailureAction: Audit`, re-apply it, apply a
violating pod, and read `kubectl get policyreport -A`. Then flip it back to `Enforce` and re-apply the
violating pod.

> **▸ On track if:** under `Audit` the violating pod **runs** but a `policyreport` records the violation;
> under `Enforce` the same pod is **blocked**. **Record** one sentence on why a real cluster starts every
> policy in `Audit`.

### Step 4 — A camera for the gap: misbehave inside a *compliant* pod

**Concept (30 sec):** Flight-card #6. The bouncer read the spec; it cannot see what an admitted pod
*does*. Falco can.

**Do it:** in a **second terminal**, `make logs-falco`. Re-admit the compliant pod
(`kubectl apply -f manifests/pod-good.yaml`), then do the thing the manifest never revealed:

```bash
kubectl exec lab-compliant -- sh -c 'cat /etc/passwd'
```

> **▸ On track if:** Falco emits the seed rule **`Read Sensitive File in Kubernetes Pod`** at priority
> `WARNING`, with `pod=lab-compliant` in the output. Ask yourself: *could any Kyverno policy have
> prevented this?* (No — the spec was compliant; the *behavior* is the signal. That is the gap.)

### Step 5 — Write your own runtime rule for the pivot

**Concept (30 sec):** Graboid's heirs land via a foothold and then run a dropped tool to pivot. Watch for
a process executing from a world-writable dir.

**Do it:** in `manifests/falco-runtime-rules.yaml` there is a seed rule **`Execution from /tmp in
Container`**. Tune it (tighten the `condition` / clarify the `output` with `%k8s.pod.name` and a
`priority`), reload Falco (`make reset`, or re-run the Helm install), and trigger it — then confirm a
benign in-container process does **not** fire it:

```bash
kubectl exec lab-compliant -- sh -c 'cp /bin/sh /tmp/sh && /tmp/sh -c id'
```

> **▸ On track if:** **your** rule fires at `CRITICAL` on the `/tmp` execution with pod context, and a
> normal command (e.g. `kubectl exec lab-compliant -- id`) stays quiet. A rule that fires on everything
> is noise nobody reads.

---

## Prove the control (your finish line)

One preventive + detective pair, re-checked against the honesty bar:

1. **Blocked at the door** — `kubectl apply -f manifests/pod-bad.yaml` is **denied** with a Kyverno error
   quoting the policy and field, *and* each of your two new policies denies a violating pod while
   admitting a compliant one.
2. **Caught at runtime** — a runtime event inside the *compliant* pod (`/etc/passwd` read **and** your
   `/tmp`-exec) each fire a Falco rule with `pod=lab-compliant` context, and a benign process does not.

If a bad pod both **can't start** *and* the thing that slips past **gets seen**, you've built the pair.
Score your four README "Call it" predictions against what actually blocked; note any you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why do you need **both** admission control and runtime detection — what is each blind to?
2. Of the four "never admit" specs, which is most common, and why is "nothing set" dangerous?
3. Why roll a Kyverno policy out in `Audit` before `Enforce` — and how do you *prove* a `deny` blocks the
   right field?

---

## Deliverables

- `manifests/policies/disallow-host-path.yaml` and `disallow-host-namespaces.yaml` — your two new
  admission policies (the prevention-as-code).
- `manifests/falco-runtime-rules.yaml` — with your tuned `/tmp`-execution rule (the detection for the gap).
- `policy-report.md` — admit/deny results with the **exact** Kyverno errors, the `Audit`→`Enforce` note,
  your Falco alert text, and the one-line answer to *which Part-3/4 actions admission could have
  prevented, and why the answer is "none."*

Commit these four. Cluster state, kubeconfigs, and secret values stay out of the commit.

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your four "never admit" verdicts only hold if a
policy *proves* them on every change, not just when you remember to apply it. Write a CI gate
(`validate-policies.yaml`, a GitHub Actions workflow) that runs the **`kyverno` CLI** (`kyverno apply`)
to dry-run *all* your policies against the manifests in the repo — **no live cluster** — and **fails the
build** when `pod-bad.yaml` (or a host-path / host-namespace pod) is admitted, and **passes** when
`pod-good.yaml` is. Have a model draft the workflow; **read every line** and confirm three things: it runs
`kyverno apply`, not `kubectl apply`; it fails on a denied manifest for the *right* policy; and it
succeeds on the compliant one. This is the bouncer encoded so a bad pod can't merge to the cluster config
in the first place — your verdict, made un-recurrable, exactly the gate the capstone reuses.

## Definition of done (`kubernetes-admission-runtime` ✅)

- [ ] `kubectl apply -f manifests/pod-bad.yaml` is denied with a Kyverno error quoting the policy and field; `pod-good.yaml` reaches `Running`.
- [ ] Your `disallow-host-path` and `disallow-host-namespaces` policies each **deny** a violating pod and **admit** a compliant one — verified, not assumed.
- [ ] You demonstrated the `Audit`→`Enforce` flip on one policy and can say in one sentence why production starts in `Audit`.
- [ ] Your tuned Falco rule fires on the `/tmp` execution with pod context and does **not** fire on a benign process.
- [ ] You can answer in writing: *which of the runtime actions could admission policy have prevented, and why is the answer "none"?*

## Connects forward

- The policies here are what module 14's `stratus-red-team` / Kubernetes attacks try to bypass — your
  door is the thing the purple-team probes.
- Falco's structured JSON output becomes the detection signal that module 15 ingests into a SIEM and
  correlates; module 16 reconstructs an incident from it.
- The `kyverno apply` CI gate is a direct sibling of the IaC gate from module 06 and the
  RBAC/NetworkPolicy-as-code from module 12 — all converge in the **capstone**, where a green pipeline
  rebuilds the *hardened* cluster and the gate fails the *original* permissive config.

## Marketable proof

> "I write Kubernetes admission policy as code — denying privileged, host-mount, host-namespace, and root
> pods at the API server before they start — roll it out `Audit`→`Enforce` the safe way, gate it in CI
> with the Kyverno CLI, and layer a tuned Falco rule for the runtime behavior admission can't see. I can
> explain why prevention without detection is blind to its own gaps."

## Stretch

- Add a Kyverno **mutate** policy that auto-injects `runAsNonRoot: true` and
  `allowPrivilegeEscalation: false` into any pod missing them, and confirm `kubectl describe pod` shows
  the mutated values — defense that doesn't depend on the developer.
- Write a Kyverno **generate** policy that drops a default-deny NetworkPolicy into every new namespace
  (the module-12 control, applied automatically) — closing the lateral-movement path Graboid used to hop
  hosts.
- Wire Falco output to a webhook (a local HTTP listener or `ngrok`) so the `/tmp`-exec alert lands
  somewhere a responder would actually see it.
