# Lab 07 — Microsegmentation: prove the deny path holds under attack

> **Hands-on lab.** Environment: `plaintext-labs/ztna/07-microsegmentation`.
> Objective: **stand up a default-deny Cilium policy, prove the allow+deny pair, then break your own
> deny path and confirm it still drops.** Target: **~90 min**, one finish line. This is a **real
> container lab** — kind + Cilium + a three-tier app; `make up` builds a live cluster.

---

## ✈ Flight card — the 7 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The exploit is replaceable; the flat interior is the multiplier.** | Patching SMBv1 wouldn't have saved Maersk — the *topology* let one box own 49,000. |
| 2 | **Default = deny; presence of an ingress rule flips a pod to default-deny.** | You don't write "deny frontend" — you write the *allow*, and everything else drops. |
| 3 | **Rules are label-scoped, not IP-scoped.** | Pod IPs churn on restart; labels follow the workload. Name the workload, not the address. |
| 4 | **Enforcement is in-kernel (eBPF), on the sending node.** | No path around the boundary — even a same-node pod goes through the hook. |
| 5 | **A deny you only read is theater — prove it, then pivot.** | Direct-IP dial + a relabelled attacker pod. The deny is real only if it survives an attempt. |
| 6 | **Default-deny silently breaks DNS.** | Forget the port-53/kube-system allow and name resolution dies — looks like an app bug. |
| 7 | **`app: backend` alone matches *any* namespace.** | Bind app **AND** namespace, or an attacker's relabelled pod inherits the allow. |

*(If you can explain all seven cold at the end — especially #1 and #5 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [reveal section](README.md#the-reveal-the-flat-interior-is-the-bug-not-the-exploit) and the
> [policy-enforcement flow](README.md#the-reveal-the-flat-interior-is-the-bug-not-the-exploit).

---

## Warm-up — answer before you touch the cluster (2 min)

*Don't scroll. Being forced to retrieve is what builds the memory.*

1. You apply an ingress policy that allows only `app: backend` to the database. You wrote **no** deny
   rule for frontend. Why is frontend now denied anyway? (Hint: flight-card #2.)
2. Your policy works, but the database pod suddenly can't resolve `backend.backend.svc`. You never
   touched DNS. What did the default-deny most likely swallow?

---

## Setup

The environment lives in the companion `plaintext-labs` repo. It builds a **real kind cluster** with
Cilium as the CNI and a three-tier `traefik/whoami` app across three namespaces (`frontend`,
`backend`, `database`). Requires **Docker**, **kind**, **kubectl**, and **helm** on your host.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/07-microsegmentation
make up       # ~3–5 min: create kind cluster, install Cilium 1.15.6, deploy the 3-tier app (allow-all, no policy yet)
make demo     # before/after: flat allow → apply policy → allow (backend→db) + deny (frontend→db)
make shell    # shell in the frontend pod for manual pivot attempts
make verify   # the allow+deny regression test you build in "Automate & own it"
make down     # delete the cluster
```

> **▸ On track if:** `make up` ends with *"Cluster is running with default allow-all (no policy yet)"*
> and `kubectl get pods -A` shows `frontend`, `backend`, `database` each `Running`. The policy you'll
> apply is **`data/database-policy.yaml`**; the app manifests are **`data/manifests.yaml`**.

> **Authorization note.** Everything runs locally in your own kind cluster — no external targets. The
> "try to pivot anyway" steps are aimed *at your own lab cluster* to prove the segmentation holds. The
> binding rule still applies elsewhere: only test systems you own or have explicit written permission
> to test.

---

## Build it — read a little, do a little

### Step 1 — Audit the flat baseline (your "before")

**Concept (30 sec):** Flight-card #1. With no policy, the interior is Maersk-flat — any pod reaches any
pod. You need to *see* the open path before you close it, or you can't prove you closed anything.

**Do it:** with no policy applied yet, dial the database from the frontend pod:

```bash
kubectl exec -n frontend deploy/frontend -- \
  curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}\n"
```

> **▸ On track if:** you get **`200`**. That 200 is the flat interior you are about to close — record
> it in `notes.md` as the "before." (If it times out, the cluster isn't up yet — re-check `make up`.)

### Step 2 — Read the policy before you apply it

**Concept (30 sec):** Flight-card #2 + #6. Open `data/database-policy.yaml`. Find the
`endpointSelector` (which pods this policy *governs* — `tier: database`), the `fromEndpoints` (which
pods are *allowed* ingress — `app: backend`), and the explicit **port-53 / kube-system** allow for DNS.

**Do it:** answer *before applying* — what makes everything except backend deny? (Answer: the mere
presence of an ingress rule on the database pods flips them to default-deny; you never wrote a "deny
frontend" line.) Note that the shipped `fromEndpoints` is `app: backend` with **no namespace** — the
soft spot you'll exploit and then close in Step 5.

> **▸ On track if:** you can point to the exact three blocks — the `tier: database` selector, the
> `app: backend` ingress allow, and the port-53 DNS allow — and say which one flips the default to deny.

### Step 3 — Apply it and prove the allow+deny pair

**Concept (30 sec):** Flight-card #5. This is the whole point: the legitimate path stays open, the
illegitimate one drops. `make demo` runs the full before/after for you — read *every* line.

**Do it:** apply the policy and test both cases.

```bash
kubectl apply -f data/database-policy.yaml
sleep 5   # let the policy propagate

# ALLOW — backend → database must still succeed:
kubectl exec -n backend deploy/backend -- \
  curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}\n"

# DENY — frontend → database must now drop:
kubectl exec -n frontend deploy/frontend -- \
  curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}\n"
```

> **▸ On track if:** backend→db returns **`200`** and frontend→db **times out** (curl exits non-zero,
> no status) — a *timeout*, not connection-refused. Cilium drops silently (no TCP RST), so the attacker
> gets no signal. If backend→db *also* fails, your allow is too tight — that's a broken policy, not a
> strict one; fix it before moving on.

### Step 4 — Capture the verdict (your audit trail)

**Concept (30 sec):** The drop is only useful if it's *observable*. `cilium monitor` gives you the
per-flow record — source pod, destination, port, policy verdict — the same telemetry Module 09 detects
lateral movement on.

**Do it:** in a second terminal, watch live drops, then repeat the frontend→db dial from Step 3:

```bash
kubectl exec -n kube-system ds/cilium -c cilium-agent -- cilium monitor --type drop
```

> **▸ On track if:** you see a **drop event** naming the frontend source, the database destination,
> port 80, and a policy-denied verdict. Paste one drop line into `notes.md` — that's your evidence.

### Step 5 — Break your own deny path, then close the gap (the red-team beat)

**Concept (30 sec):** Flight-card #3 + #4 + #7. A deny you haven't attacked is a guess. Two pivots test
two claims: direct-IP dial tests "is it really label-scoped, not IP-scoped?" and a relabelled pod tests
"does the bare `app: backend` allow leak across namespaces?"

**Do it:** from a frontend foothold (`make shell`), attempt at least two bypasses and confirm each still
drops (and shows in `cilium monitor`):

- **Direct ClusterIP / pod IP** instead of the DNS name — grab it with `kubectl get svc -n database`
  and `curl` the IP. (Should still drop — the policy is label-scoped, enforced in-kernel on the sender.)
- **Relabel an attacker pod** — deploy a throwaway pod *in the frontend namespace* carrying
  `app: backend`, then dial the database from it:
  ```bash
  kubectl run evil -n frontend --image=curlimages/curl --labels=app=backend \
    --restart=Never -it --rm -- \
    curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}\n"
  ```

> **▸ On track if:** the direct-IP dial **drops**, but the relabelled `evil` pod **reaches the database
> (`200`)** — the bare `app: backend` allow leaked across namespaces. That leak *is* the lesson.

**Close it:** tighten `fromEndpoints` in `data/database-policy.yaml` to require **both** the app label
*and* the backend namespace, re-apply, and re-run the `evil` pivot:

```yaml
ingress:
  - fromEndpoints:
      - matchLabels:
          app: backend
          k8s:io.kubernetes.pod.namespace: backend
```

> **▸ On track if:** after re-apply, the relabelled `evil` pod is now **denied** (timeout) while the
> real backend→db path still returns **`200`**. In one sentence, `notes.md`: why naming a workload
> (`app` **and** namespace) beats naming a string (`app` alone that any namespace can copy).

---

## Prove the control (your finish line)

One command that proves the pair holds — the legitimate path open, the denied path closed:

```bash
make verify
```

**The proof (a blocked-then-allowed pair):** `make verify` must show **backend→db PASS** (the allow
stays open) *and* **frontend→db PASS** (the deny stays closed — the test passes *because* the
connection fails). If someone later re-allows frontend or drops the namespace constraint, this goes
**red**. That red is the entire point: *a default-deny you can't re-prove on demand is one you've
stopped trusting.*

---

## Recall check — close the cluster docs, answer from memory (3 min)

1. Maersk was patched the next week and the flat network was still there — which control actually shrinks the blast radius, the patch or the policy, and why?
2. You wrote only an *allow* rule. Why is frontend denied, and what exactly flipped the default?
3. Name the two pivots you ran against your own deny path — which dropped, which leaked before you tightened the selector, and why?

Missed one? Re-run the step that built it, or pull the [module reveal](README.md#the-reveal-the-flat-interior-is-the-bug-not-the-exploit) — then re-answer.

---

## Deliverables

- **`database-policy.yaml`** — your final, *tightened* default-deny Cilium policy (app **and**
  namespace bound; DNS allowed). A portfolio artifact: it shows you can express segmentation as
  label-scoped policy-as-code.
- **`notes.md`** — the flat baseline `200`, the captured `cilium monitor` drop line, the pivot results
  (which dropped, which leaked and why), and the one-sentence label-scope analysis.
- **`verify-policy.sh`** — the allow+deny regression test (below), wired to `make verify`.

*Kubeconfig, cluster state, and captured flow logs are ephemeral lab artifacts — they stay out of
commits (they're in `.gitignore`).*

## Automate & own it

**Required — turn the allow+deny pair into a regression test (the Judgment-as-Code beat).** Write
`verify-policy.sh` that:

1. Runs `kubectl exec curl` from **backend → database** and asserts it **succeeds** (exit 0 / HTTP 200)
   — the legitimate path stays open.
2. Runs `kubectl exec curl` from **frontend → database** and asserts it **fails** (non-zero / timeout)
   — the denied path stays closed.
3. Exits 0 only when *both* hold; exits 1 with a clear per-case message otherwise.

Have a model draft it — then **read every line**, especially that the deny assertion **fails closed**:
a `curl` that errors for the *wrong* reason, or a step that can't run at all, must count as a
**failure**, not a silent pass. Wire it as the `make verify` target. If someone edits the policy and
accidentally re-flattens the network — re-allowing frontend, or dropping the namespace constraint —
this test goes red. Commit `verify-policy.sh` alongside the policy and notes.

## Definition of done (`microsegmentation` ✅)

- [ ] `make demo` shows the flat baseline (frontend→db 200), then — after the policy — allow (backend→db 200) and deny (frontend→db timeout), clearly labelled.
- [ ] A real `cilium monitor` **drop event** for the frontend→db attempt is captured in `notes.md`.
- [ ] You ran both pivots (direct IP, relabelled pod), documented which dropped and which leaked, and the deny path held under the active attempt.
- [ ] The selector is tightened to bind `app: backend` **and** the backend namespace; the relabel pivot is now denied and the legitimate backend→db path still succeeds.
- [ ] `make verify` passes (allow holds, deny holds) and would go red if frontend→db were re-allowed.
- [ ] `database-policy.yaml` + `notes.md` + `verify-policy.sh` are committed; you can explain all seven flight-card facts cold.

## Connects forward

- **Module 09 — Monitoring & Detection** turns the Cilium drop events you captured into a
  lateral-movement detection: a Sigma rule over Cilium drops alerts on *any pod outside `backend`
  reaching `database`.* Your `notes.md` drop line is its raw material.
- The **Red-team-your-own-deployment** module (Type 10) scales the "prove the deny under an active
  attempt" discipline to the whole gated service, end to end.
- The **VPN → ZTNA migration** (Type 12, Module 10) must establish exactly this default-deny baseline as
  it moves apps off the flat network one cohort at a time — the direct sequel to Module 01's indictment.

## Marketable proof

> "I deploy Cilium microsegmentation in a Kubernetes cluster as default-deny policy-as-code, prove the
> allow and deny cases at the workload level, and harden the policy against a real pivot — a relabelled
> attacker pod — with a regression test that goes red the moment the network is re-flattened."

## Stretch

- Enable **Hubble** (`cilium hubble enable`) and read the drop events with `hubble observe --verdict
  DROPPED` and the Hubble UI flow graph — the same audit trail without `cilium monitor`.
- Add an **egress** policy on the `database` namespace: database pods may only respond to `backend` and
  reach kube-dns, nothing else. Confirm the database can no longer initiate an outbound connection —
  the data-exfil path NotPetya-style malware would use.
- Apply a **Layer-7** policy with Cilium's HTTP-aware rules: allow `backend → database` only on path
  `/api/v1`, deny all other paths. Confirm with `curl` — segmentation down to the request, not just the
  port.
