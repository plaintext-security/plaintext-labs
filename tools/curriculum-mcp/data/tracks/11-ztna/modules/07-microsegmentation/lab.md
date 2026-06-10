# Lab 07 — Microsegmentation with Cilium

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This lab requires **Docker**, **kind**, and **kubectl** installed on your host.

- Install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation
- Install kubectl: https://kubernetes.io/docs/tasks/tools/

The lab environment is in the companion [`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/07-microsegmentation
make up      # create the kind cluster, install Cilium, deploy the three-tier app
make demo    # show the allow case (frontend→backend) and the deny case (frontend→database)
make shell   # open a shell in the frontend pod for manual testing
make down    # delete the kind cluster
```

`make up` takes approximately 3–5 minutes the first time (pulls kind node image and Cilium images). Subsequent `make up` calls are faster if images are cached locally.

> Everything runs in local containers. No external targets, no cloud accounts required. Only test systems you own or have explicit written permission to test.

## Scenario

Meridian Financial's Kubernetes platform team has a cluster running three application tiers in separate namespaces: `frontend` (web tier), `backend` (API tier), and `database` (PostgreSQL tier). Currently there are no network policies — every pod can reach every other pod. After a recent pen-test finding that flagged east-west lateral movement risk, the security team wants to enforce database isolation: **only the backend tier should reach the database, and frontend should be explicitly denied.**

You will deploy the Cilium policies that enforce this, verify the allow and deny cases, and trace the policy decision in Cilium's observability output.

## Do

1. [ ] **Audit the baseline (pre-policy).** After `make up`, confirm the default allow-all posture:
   ```bash
   kubectl exec -n frontend deploy/frontend -- curl -s http://database.database.svc.cluster.local:80 -m 3
   ```
   This should succeed (or return a TCP response, not a connection refused). Note the output — this is the open posture you are about to close.

2. [ ] **Apply the Cilium network policy.** Review `data/database-policy.yaml` — understand the `endpointSelector` (which pods are governed) and the `fromEndpoints` (which pods are allowed ingress). Then apply it:
   ```bash
   kubectl apply -f data/database-policy.yaml
   ```

3. [ ] **Verify the allow case.** From the backend namespace, reach the database — this should succeed:
   ```bash
   kubectl exec -n backend deploy/backend -- curl -s http://database.database.svc.cluster.local:80 -m 3
   ```

4. [ ] **Verify the deny case.** From the frontend namespace, attempt to reach the database — this must now be denied:
   ```bash
   kubectl exec -n frontend deploy/frontend -- curl -s http://database.database.svc.cluster.local:80 -m 3
   ```
   The connection should time out (Cilium drops silently by default, no TCP RST). Note the exact failure mode.

5. [ ] **Watch the policy decision in real time.** In a second terminal, run:
   ```bash
   kubectl exec -n kube-system ds/cilium -c cilium-agent -- cilium monitor --type drop
   ```
   Then repeat the denied `curl` from step 4. You should see a drop event with the source pod, destination pod, port, and the policy verdict. This is your audit trail.

6. [ ] **Reason about gaps.** The policy allows `app: backend → tier: database`. What happens if someone adds a new pod in the `backend` namespace with a different label? Would it be allowed or denied? Adjust the policy to require *both* `app: backend` *and* `namespace: backend` in the `fromEndpoints` selector, and explain why this tightens the policy.

## Success criteria — you're done when

- [ ] `kubectl exec` from the `frontend` namespace to the `database` service times out (denied).
- [ ] `kubectl exec` from the `backend` namespace to the `database` service succeeds (allowed).
- [ ] A Cilium monitor drop event is visible when the denied request is made.
- [ ] You've explained the label-scope gap (step 6) and adjusted the policy to address it.

## Deliverables

- `database-policy.yaml` — your final (tightened) Cilium network policy
- `notes.md` — the baseline finding, the drop event output from `cilium monitor`, and your label-scope analysis from step 6

Commit both. Kubeconfig files and cluster state are ephemeral — they are not committed.

## Automate & own it

**Required.** Write a script `verify-policy.sh` that:
1. Runs the `kubectl exec curl` from `frontend → database` and asserts the exit code is non-zero (connection denied or timed out)
2. Runs the `kubectl exec curl` from `backend → database` and asserts the exit code is zero (connection succeeds)
3. Exits 0 on pass, 1 on failure, with a message for each case

Have a model draft it; **you read every line**. Wire it as `make verify`. This is a lightweight policy regression test — if someone changes the policy and accidentally re-allows frontend, `make verify` catches it.

## AI acceleration

Describe your segmentation intent in plain English to a model: "Backend pods in the backend namespace should reach database pods in the database namespace on port 80. All other ingress to database pods should be denied, including from the frontend namespace." Ask it to generate the `CiliumNetworkPolicy`. Then test both the allow and deny cases — AI-generated label selectors often miss namespace constraints (see step 6).

## Connects forward

These Cilium flow logs — particularly the drop events — are structured telemetry that module 09 uses for detection. A Sigma rule over Cilium drop logs can detect lateral movement attempts: "any pod outside the `backend` namespace attempting to reach the `database` namespace" is a finding worth alerting on.

## Marketable proof

> "I can deploy Cilium microsegmentation in a Kubernetes cluster, enforce a default-deny posture with explicit allow rules, and produce audit logs that prove lateral movement between tiers is blocked."

## Stretch

- Enable **Hubble** (Cilium's observability UI) with `cilium hubble enable` and view the traffic flow graph in Hubble UI. Export the flow logs and identify the drop events without using `cilium monitor`.
- Write a `CiliumNetworkPolicy` that also restricts egress from the `database` namespace — database pods should only be able to respond to `backend` pods and reach the kube-dns service, nothing else.
- Apply a Layer 7 policy using Cilium's HTTP-aware rules: allow `backend → database` only on path `/api/v1`, deny all other paths. Confirm with `curl`.
