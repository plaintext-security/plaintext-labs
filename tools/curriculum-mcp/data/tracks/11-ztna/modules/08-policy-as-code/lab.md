# Lab 08 — Policy as Code with OPA

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/08-policy-as-code
make up      # build + start the OPA container
make demo    # run both policy scenarios (allow and deny cases for each)
make shell   # drop into the container to experiment with opa eval interactively
make down    # stop it when you're done
```

The container bundles `opa` (the real binary, not a simulator) and your policy/input files mounted from `data/`. Every `make` target runs `opa eval` with real Rego evaluation — no mocks.

> Everything runs locally against bundled data you own. No external targets, no authorization needed.

## Scenario

Meridian Financial's security team is replacing ad-hoc role checks scattered across three internal APIs with a centralized OPA policy sidecar. They have two immediate requirements:

1. **Data access policy:** Analyst users can read financial records but not write them. Admins can do both. Service accounts used by automated reports are read-only. The policy must evaluate JWT claims, not application-level session state.

2. **Kubernetes admission policy:** No pod in the cluster may run as root (`runAsUser: 0` or an omitted `runAsUser` in `securityContext`). The security team has seen three incidents where a container escape from a root-running pod led to host compromise.

You will write and test both policies, show the AI-drafting → deny-path-validation workflow, and commit a working `opa test` suite.

## Do

**Scenario 1 — Data access by role**

1. [ ] **Read the policy and inputs.** Open `data/policies/data-access.rego` — understand the `allow` and `deny` rules and which JWT claims they check. Then look at the four input files in `data/inputs/` (`analyst-read.json`, `analyst-write.json`, `admin-write.json`, `service-account-write.json`).

2. [ ] `make demo` — watch all four cases run. Note which cases produce `{"allow": true}` and which produce `{"allow": false}`. The output labels each case. Confirm the results match your reading of the policy.

3. [ ] **Add a new role.** The compliance team wants a `auditor` role that can read but not write, and specifically cannot call the `/export` path (which downloads bulk data). Extend `data-access.rego` to deny `auditor` on path `/export` regardless of action. Add an input file `data/inputs/auditor-export.json` that represents this case and confirm the denial with:
   ```bash
   make eval POLICY=data/policies/data-access.rego INPUT=data/inputs/auditor-export.json
   ```

4. [ ] **Write a test.** OPA has a built-in test runner. Add at least two test cases to `data/policies/data-access_test.rego` (the file exists, add to it): one that asserts the analyst-write case is denied, and one that asserts the auditor-export case is denied. Run:
   ```bash
   make test
   ```
   Both tests must pass.

**Scenario 2 — Kubernetes admission**

5. [ ] **Read the admission policy.** Open `data/policies/k8s-admission.rego`. Understand how it extracts `runAsUser` from the pod spec's security context. Note the two cases it must cover: explicit `runAsUser: 0` and omitted `runAsUser` (default behavior is root on many images).

6. [ ] **Test both deny cases.** The demo already runs both — but run them manually to see the full OPA output:
   ```bash
   make eval POLICY=data/policies/k8s-admission.rego INPUT=data/inputs/pod-root.json
   make eval POLICY=data/policies/k8s-admission.rego INPUT=data/inputs/pod-no-user.json
   ```
   Confirm both return `{"deny": true, ...}`.

7. [ ] **Test the allow case.**
   ```bash
   make eval POLICY=data/policies/k8s-admission.rego INPUT=data/inputs/pod-nonroot.json
   ```
   Confirm this returns `{"deny": false}` (or `{"allow": true}` depending on your policy shape — check which query the demo uses).

8. [ ] **The AI drafting exercise.** Ask a model: "Write an OPA Rego policy that denies Kubernetes pods that do not set `readOnlyRootFilesystem: true` in their container securityContext." Paste the result into `data/policies/readonly-fs.rego`. Then write an input JSON `data/inputs/pod-writable-fs.json` and a test in `data/policies/readonly-fs_test.rego`. Run `make test` and confirm the deny case is covered. The point: validate the AI's deny path before shipping.

## Success criteria — you're done when

- [ ] `make demo` shows all labelled allow/deny cases for both scenarios cleanly.
- [ ] The `auditor` role is denied on `/export` and your new test case covers it.
- [ ] `make test` passes all test cases including the ones you wrote.
- [ ] The `readonly-fs` policy from step 8 has a passing deny-path test.

## Deliverables

- `data/policies/data-access.rego` — the extended policy with the auditor/export rule
- `data/policies/data-access_test.rego` — the test suite including your new cases
- `data/policies/readonly-fs.rego` — the AI-drafted read-only filesystem policy
- `data/policies/readonly-fs_test.rego` — its deny-path test
- `data/inputs/auditor-export.json` and `data/inputs/pod-writable-fs.json` — the new inputs

Commit all of the above. The git history is the audit trail for who changed what policy and when.

## Automate & own it

**Required.** Add a `make ci` target that runs `opa test ./data/policies/` over every policy file. Wire a GitHub Actions workflow `.github/workflows/opa-test.yml` that runs this on every push. Have a model draft the workflow; **you read every line** and confirm the `opa test` command matches what you run locally. A policy change that breaks a test should block merge — that is policy-as-code for real.

## AI acceleration

AI is fluent at Rego for common patterns: RBAC, Kubernetes admission, JWT claim checks. Use it to draft policies quickly, then always run `opa eval` against at least one input that should be denied. If the output is `{}` (empty, no result) rather than `{"allow": false}`, your query path is wrong — the rule fired no result. This is the most common OPA gotcha and the one AI drafts won't warn you about.

## Connects forward

OPA integrates with Pomerium (module 06) as an external authorization provider: Pomerium calls OPA on every request with the JWT claims, and OPA returns allow/deny based on fine-grained policy. This lets you keep coarse authentication in Pomerium and fine-grained authorization in OPA, with the authorization logic version-controlled and tested independently of the proxy configuration.

## Marketable proof

> "I write and test OPA Rego policies for RBAC and Kubernetes admission control, version them in git with a `opa test` CI suite, and validate both allow and deny paths before deployment."

## Stretch

- Integrate OPA with Pomerium using `policy.rego` in a Pomerium route: write a Rego policy that Pomerium evaluates per-request instead of YAML `allow` stanzas. This is the production pattern for complex authorization.
- Write a policy that uses OPA's `http.send` built-in to fetch an external data source (an ACL JSON file served by a local nginx container) and evaluate access against it. This demonstrates the "external data" pattern for policies that need live data rather than bundled documents.
