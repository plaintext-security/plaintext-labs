# Lab 07 — Microsegmentation with Cilium

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate.** You stand up a default-deny segmentation policy in a real kind cluster,
run it, and prove the thing that actually makes it Zero Trust: the **deny path holds — even when you
try to pivot around it.** The deliverable is the *default-deny policy-as-code + the proven allow+deny
pair* — not a writeup. No grader; you verify your own work against the observable success criteria
below. (Honor system: the committed policy, notes, and regression test are the proof.)

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It requires **Docker**,
**kind**, **kubectl**, and **helm** on your host.

- Install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation
- Install kubectl: https://kubernetes.io/docs/tasks/tools/
- Install helm: https://helm.sh/docs/intro/install/

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/07-microsegmentation
make up      # create the kind cluster, install Cilium, deploy the three-tier app (allow-all, no policy yet)
make demo    # show the before/after: allow-all → apply policy → allow (backend→db) + deny (frontend→db)
make shell   # open a shell in the frontend pod for manual pivot attempts
make verify  # the allow+deny regression test you build in "Automate & own it"
make down    # delete the kind cluster
```

`make up` takes ~3–5 minutes the first time (it pulls the kind node image and Cilium images). The app
is three single-pod tiers in three namespaces (`frontend`, `backend`, `database`), each a
`traefik/whoami` container that echoes request headers and returns 200 — enough to demonstrate
allow/deny connectivity without application complexity.

> **Authorization note:** Only test systems you own or have explicit written permission to test.
> Everything here runs locally in your own kind cluster — no external targets. The "try to pivot
> anyway" steps below are aimed *at your own lab cluster* to prove the segmentation holds.

## Scenario

A platform team runs a three-tier app — `frontend` (web), `backend` (API), `database` (data) — in one
Kubernetes cluster with **no network policies**: every pod can reach every other pod, the flat interior
that turned a single foothold into a company-wide incident at Maersk in 2017. A pen-test just flagged
the east-west lateral-movement risk. Your job: enforce database isolation as **default-deny + an
explicit allow** — only the backend tier reaches the database; frontend is denied — prove both halves,
then attempt to pivot around the policy and confirm it still drops.

## Do

Stand up the default-deny posture, prove the allow+deny pair, then attack your own deny path until
you've proven it closed.

**Build & operate the segmentation policy**
1. [ ] **Audit the flat baseline.** After `make up` (before any policy), confirm the open posture —
   frontend can reach the database:
   ```bash
   kubectl exec -n frontend deploy/frontend -- \
     curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}\n"
   ```
   A `200` here is the flat interior you are about to close. Record it — it is your "before."
2. [ ] **Read the policy before you apply it.** Open `data/database-policy.yaml`. Identify the
   `endpointSelector` (which pods this policy *governs* — `tier: database`) and the `fromEndpoints`
   (which pods are *allowed* ingress — `app: backend`), and note the explicit **port-53 / kube-system
   allow** for DNS. Then ask yourself, before applying: *what makes everything else deny?* (Answer: the
   mere presence of an ingress rule on the database pods flips them to default-deny.)
3. [ ] **Apply it and watch the posture flip.** `kubectl apply -f data/database-policy.yaml`, wait a few
   seconds for propagation. (`make demo` runs the full before/after sequence for you — read every line
   of its output.)

**Prove the allow+deny pair**
4. [ ] **Verify the allow case** — backend→db must still succeed:
   ```bash
   kubectl exec -n backend deploy/backend -- \
     curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}\n"
   ```
   Expect `200`. (If this fails, the allow is too tight — fix it before moving on; a default-deny that
   also denies the legitimate path is a broken policy, not a strict one.)
5. [ ] **Verify the deny case** — frontend→db must now drop:
   ```bash
   kubectl exec -n frontend deploy/frontend -- \
     curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}\n"
   ```
   Expect a **timeout**, not a connection-refused — Cilium drops silently by default (no TCP RST).
   Note the exact failure mode; the *silent drop* is itself the lesson (an attacker gets no signal).
6. [ ] **See the verdict.** In a second terminal, watch live drops, then repeat step 5:
   ```bash
   kubectl exec -n kube-system ds/cilium -c cilium-agent -- cilium monitor --type drop
   ```
   You should see a drop event with source pod, destination, port, and the policy verdict. This is your
   audit trail — capture one drop line for `notes.md`. (Stretch: enable Hubble and read the same drop
   with `hubble observe --verdict DROPPED`.)

**Try to pivot anyway (the red-team beat)**
7. [ ] **Attempt the bypass.** The deny is only real if it survives an active attempt to get around it.
   From a foothold in the `frontend` pod (`make shell`), try at least two pivots and confirm **each
   still drops** (and shows up in `cilium monitor`):
   - **Dial the service ClusterIP / pod IP directly** instead of the DNS name (does an IP-scoped escape
     exist? It shouldn't — the policy is label-scoped, enforced in-kernel on the sending node).
   - **Relabel an attacker pod.** Deploy a throwaway pod *in the frontend namespace* carrying
     `app: backend` and try the reach from it. Does the bare app-label allow let it through? Document
     what happens — this is the label-scope gap in action.

   In `notes.md`, state plainly: which pivots dropped, which (if any) succeeded, and *why*.
8. [ ] **Close the gap you found.** Tighten `fromEndpoints` to require **both** `app: backend` *and* the
   backend namespace (`k8s:io.kubernetes.pod.namespace: backend`), re-apply, and re-run step 7's relabel
   pivot. Confirm the attacker pod is now denied while the real backend still reaches the database.
   Explain in one sentence why naming a workload (`app` **and** namespace) beats naming a string
   (`app` alone that any namespace can copy).

## Success criteria — you're done when

- [ ] `make demo` shows the flat baseline, then — after the policy — the allow case (backend→db, 200)
      and the deny case (frontend→db, timeout), clearly labelled.
- [ ] You captured a real `cilium monitor` **drop event** for the frontend→db attempt in `notes.md`.
- [ ] You ran the pivot attempts (direct IP, relabelled pod) and documented which dropped and why — and
      the deny path stayed closed under the active attempt.
- [ ] You tightened the selector to bind `app: backend` **and** the backend namespace, re-proved the
      relabel pivot is now denied, and the legitimate backend→db path still succeeds.
- [ ] `make verify` passes (allow holds, deny holds) and would go red if frontend→db were re-allowed.

## Deliverables

- `database-policy.yaml` — your final, tightened default-deny Cilium network policy (app **and**
  namespace bound; DNS allowed).
- `notes.md` — the flat baseline finding, the captured `cilium monitor` drop line, the pivot results
  (what dropped / what succeeded and why), and the label-scope analysis.

Commit both. Kubeconfig files, cluster state, and any captured flow logs are ephemeral lab artifacts —
they stay out of commits (they're in `.gitignore`).

## Automate & own it

**Required — this is the allow+deny pair turned into a regression test (the secondary Judgment-as-Code
beat).** Write `verify-policy.sh` that:
1. Runs the `kubectl exec curl` from **backend → database** and asserts the connection **succeeds**
   (exit 0 / HTTP 200) — the legitimate path stays open.
2. Runs the `kubectl exec curl` from **frontend → database** and asserts the connection **fails**
   (non-zero exit / timeout) — the denied path stays closed.
3. Exits 0 only when *both* hold; exits 1 with a clear per-case message otherwise.

Have a model draft it; **you read every line** before trusting it — especially that the deny assertion
fails *closed* (a `curl` that errors for the *wrong* reason, or a step that can't run, must count as a
failure, not a silent pass). Wire it as the `make verify` target. This is your segmentation regression
test: if someone edits the policy and accidentally re-flattens the network — re-allowing frontend, or
dropping the namespace constraint — `make verify` goes red. That red is the point; a default-deny you
can't re-prove on demand is one you've stopped actually trusting.

## AI acceleration

Describe your segmentation intent in plain English — "backend pods *in the backend namespace* reach
database pods *in the database namespace* on port 80; deny all other ingress to database pods, including
from frontend; allow DNS to kube-system" — and ask a model for the `CiliumNetworkPolicy`. Then refuse
to trust the allow path: AI-generated policy reliably (1) **omits the DNS allow** and (2) **writes a
bare app-label match with no namespace**, both of which you only catch by testing the *deny* and trying
to *pivot*. Run the relabel pivot from step 7 against the AI's draft and watch it let the attacker pod
through. The transferable skill isn't prompting for YAML; it's owning the deny path well enough to
encode it in `verify-policy.sh`.

## Connects forward

The Cilium flow logs — especially the drop events you captured — are structured telemetry that
**module 09 (Monitoring & Detection)** turns into a lateral-movement detection: a Sigma rule over
Cilium drops can alert on "any pod outside the `backend` namespace attempting to reach `database`."
The "prove the deny under an active attempt" discipline here is the warm-up for the
**Red-team-your-own-deployment** module (Type 10), which attacks the whole gated service end to end. And
the default-deny baseline is exactly the posture the **VPN → ZTNA migration** (Type 12) must establish
as it moves apps off the flat network one cohort at a time.

## Marketable proof

> "I deploy Cilium microsegmentation in a Kubernetes cluster as default-deny policy-as-code, prove the
> allow and deny cases at the workload level, and harden the policy against a real pivot — a relabelled
> attacker pod — with a regression test that goes red the moment the network is re-flattened."

## Stretch

- Enable **Hubble** (`cilium hubble enable`) and read the drop events with `hubble observe --verdict
  DROPPED` and the Hubble UI flow graph — the same audit trail without `cilium monitor`.
- Add an **egress** policy on the `database` namespace: database pods may only respond to `backend` and
  reach kube-dns, nothing else. Confirm the database can no longer initiate a connection out (the
  data-exfil path NotPetya-style malware would use).
- Apply a **Layer-7** policy with Cilium's HTTP-aware rules: allow `backend → database` only on path
  `/api/v1`, deny all other paths. Confirm with `curl` — segmentation down to the request, not just the
  port.
