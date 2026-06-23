# Lab 08 — Encode the Verdict as a Gate: Policy that Fails Closed

*Type 8 · build-first, judgment-as-code. [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/08-policy-as-code
make up      # build + start the OPA container (real opa binary, pinned)
make demo    # run both policy scenarios (allow + deny cases for each)
make shell   # drop into the container to experiment with opa eval interactively
make down    # stop it when you're done
```

The container bundles `opa` (the real binary, not a simulator) and your policy/input files mounted from `data/`. Every `make` target runs `opa eval` / `opa test` with real Rego evaluation — no mocks.

> Everything runs locally against bundled data you own. No external targets, no authorization needed.

## Scenario

An internal platform team is replacing ad-hoc role checks scattered across three APIs — and a tribal "don't run containers as root" convention nobody enforces — with centralized OPA policy. Two immediate requirements:

1. **Data access policy:** Analysts read financial records but can't write them. Admins do both. Service accounts behind automated reports are read-only. The policy evaluates JWT claims, not application-level session state.
2. **Kubernetes admission policy:** No pod may run as root — neither an explicit `runAsUser: 0` nor an *omitted* `runAsUser` (which is root by default on most images). The team has eaten container-escape incidents that started with a root pod.

Your job is not "write two policies." It is to **leave behind a gate** that fails the bad state and passes the fix, *and to catch the policy that secretly fails open* — the deny rule that looks present but never fires. The scan finds the patterns; you render the verdict on whether the policy actually denies; the gate makes the verdict un-recurrable.

The rhythm each part: **write/read the policy → run the case that MUST be denied → confirm `{"deny": [...]}` not `{}` → wire it into a gate and prove the exit code flips.**

## Do

### Part 1 — Data access by role

1. [ ] **Read the policy and inputs.** Open `data/policies/data-access.rego`. Identify `default allow = false`, the `allow` rule(s), and the `deny` rule(s), and note which JWT claims each checks (`input.user.role`, `input.action`, `input.path`). Then read the four inputs in `data/inputs/` (`analyst-read.json`, `analyst-write.json`, `admin-write.json`, `service-account-write.json`). **Predict** the verdict for each before you run anything.

2. [ ] **`make demo`** — watch all four cases run. Confirm which produce `{"allow": true}` and which produce `{"allow": false}`, and that they match your prediction. Where deny overrides allow (analyst trying to write), confirm the *deny* fired, not just that allow was absent.

3. [ ] **Add a new role with a deny the others don't have.** Compliance wants an `auditor` role that can read but **cannot** call the `/export` path (bulk download) regardless of action. Extend `data-access.rego` so `auditor` is denied on path `/export`. Add `data/inputs/auditor-export.json` and confirm the denial:
   ```bash
   make eval POLICY=data/policies/data-access.rego INPUT=data/inputs/auditor-export.json
   ```
   The output must be `{"deny": [...]}` (or `{"allow": false}` for an allow-shaped query) — **not** `{}`.

### Part 2 — The fail-open trap (the centerpiece)

4. [ ] **Plant a silently-absent deny, then catch it.** This is the lesson of the module. Make your new `auditor`/`export` deny rule subtly *wrong* in one of these realistic ways (pick one):
   - typo the claim: check `input.user.roles` (plural) when the input uses `input.user.role`;
   - flip a comparison: `input.path != "/export"` where you meant `==`;
   - guard it behind a condition that's never true for the test input.

   Re-run the `auditor-export` eval. **The denial vanishes** — you'll get `{}` or `{"allow": true}`, because the rule never fires and the default applies. **Record what you saw** in one line. This is a policy that fails *open*: it looks complete, but the rule you "wrote" denies nothing.

5. [ ] **Prove the structure that makes absence fail *closed*.** Confirm the policy uses `default allow = false` **and** that your evaluation queries the **deny set** (or an allow that is gated on no-deny), so "no rule fired" resolves to *deny*, never *allow*. Restore the correct deny rule from step 3. Re-run the eval and confirm the denial is back. The pair (broken → open, fixed → closed) is the proof you understand the trap, not the syntax.

6. [ ] **Write the tests — for the deny path, explicitly.** Add at least three cases to `data/policies/data-access_test.rego`: `test_analyst_write_denied`, `test_auditor_export_denied`, and `test_analyst_read_allowed`. Run:
   ```bash
   make test
   ```
   All must pass. Then **re-plant the step-4 bug** and run `make test` again: the deny test must now **FAIL**. A test suite that stays green while the deny rule is broken is not testing the deny path — it's testing nothing. Fix the policy, confirm green, and keep this proof.

### Part 3 — Kubernetes admission (the omitted-field trap)

7. [ ] **Read the admission policy.** Open `data/policies/k8s-admission.rego`. Note how it extracts `runAsUser` from the pod's `securityContext`, and that it must cover **two** cases: explicit `runAsUser: 0` *and* an omitted `runAsUser` (root by default). The omitted case is the one AI drafts usually miss.

8. [ ] **Test both deny cases and the allow case.**
   ```bash
   make eval POLICY=data/policies/k8s-admission.rego INPUT=data/inputs/pod-root.json
   make eval POLICY=data/policies/k8s-admission.rego INPUT=data/inputs/pod-no-user.json
   make eval POLICY=data/policies/k8s-admission.rego INPUT=data/inputs/pod-nonroot.json
   ```
   The first two must return `{"deny": [...]}`; the third must be empty/`allow`. If `pod-no-user.json` is **not** denied, the policy missed the omitted-field case — fix it and re-run. (This is the same fail-open trap as Part 2, wearing a Kubernetes costume.)

9. [ ] **The AI-drafting exercise, deny-path-first.** Ask a model: *"Write an OPA Rego policy that denies Kubernetes pods that do not set `readOnlyRootFilesystem: true` in their container securityContext."* Paste it into `data/policies/readonly-fs.rego`. Then — before trusting it — write `data/inputs/pod-writable-fs.json` (the case that must be denied) and a test in `data/policies/readonly-fs_test.rego`. Run `make test`. If the deny case isn't covered, the AI wrote the allow path and left the hole; close it yourself. Validate the deny path before shipping — every time.

### Part 4 — Encode the verdict as the gate (the deliverable)

10. [ ] **Write the CI gate.** Add a `make ci` target that runs `opa test ./data/policies/` over every policy, and a GitHub Actions workflow `.github/workflows/opa-test.yml` (on `push` + `pull_request`) that runs it. Have a model draft the workflow; **read every line** and confirm the `opa test` invocation matches what you run locally. The gate's contract:
    - it **fails** (exit non-zero) when any deny rule is broken — including the step-4 fail-open bug, the omitted-`runAsUser` miss, and a missing `readonly-fs` deny test;
    - it **passes** (exit zero) only when every deny path is proven.

11. [ ] **Prove the gate flips.** Re-plant one fail-open bug, run the gate's exact command, and check `echo $?` — it must be non-zero. Restore the fix, re-run — it must be zero. A gate whose exit code doesn't change between broken and fixed isn't a gate; it's a report. This single assertion is the whole module.

## Success criteria — you're done when

- [ ] `make demo` shows all labelled allow/deny cases for both scenarios, and you confirmed each deny *fired* (not merely that allow was absent).
- [ ] The `auditor` role is denied on `/export`, with an input and a passing `opa test` case covering it.
- [ ] You **caught a fail-open gap**: you planted a silently-absent deny rule, observed the denial vanish to `{}`/`allow`, and proved that `default allow = false` + querying the deny set makes absence fail *closed*.
- [ ] `make test` passes; and you demonstrated that re-planting the deny bug turns a deny test **FAILED** (the test actually exercises the deny path).
- [ ] The K8s admission policy denies **both** explicit-root and omitted-`runAsUser` pods; the AI-drafted `readonly-fs` policy has a passing deny-path test.
- [ ] `opa-test.yml` / the gate command exits **non-zero on a broken (fail-open) policy and zero on the fixed one** — demonstrated with `$?`.

## Deliverables

Commit to your portfolio repo:
- `data/policies/data-access.rego` — the extended policy with the auditor/export deny, structured to fail closed (`default allow = false`).
- `data/policies/data-access_test.rego` — the test suite, including the explicit deny-path cases.
- `data/policies/readonly-fs.rego` + `readonly-fs_test.rego` — the AI-drafted policy with *your* deny-path test.
- `data/inputs/auditor-export.json` and `data/inputs/pod-writable-fs.json` — the new inputs.
- `fail-open-proof.md` — the one-line record from step 4/5 (what the broken deny produced) plus the two terminal captures from step 11 (gate exit code: broken vs. fixed) proving the gate flips.
- `.github/workflows/opa-test.yml` — the CI gate.

Do **not** commit: raw `opa eval` JSON dumps, or `data/` files seeded by the lab repo that you didn't change.

The `git history` is the audit trail for who changed which policy and when — that is policy-as-code's whole point.

## Automate & own it

**Required — this is the judgment-as-code core of the module.** Your verdict is: *"these access rules must hold, and a deny rule that silently fails open must never pass review."* Encode it as a portable gate — `gate.sh`, a single script that:

1. runs `opa test ./data/policies/` (exit non-zero on any failing/erroring test), and
2. runs `opa eval` on each must-deny input and **asserts the result is a real deny, not `{}`** — so a silently-absent deny rule fails the gate instead of sliding through as an empty (allow-reading) result, and
3. prints which policy/input combination blocked it.

Then write the proof harness: with a fail-open bug planted, `gate.sh` exits 1; with it fixed, `gate.sh` exits 0; assert the flip. **Have a model draft the bash and the `opa eval` query/`jq` checks; review every line** — confirm an `opa` *error* doesn't read as a *clean pass*, and that the gate fails for the *right* reason (the missing deny), not an unrelated parse nit. This gate is your verdict made un-recurrable.

## AI acceleration

AI is fluent at Rego for RBAC, K8s admission, and JWT claim checks — and will draft the *allow* path beautifully while leaving the deny path you actually need unproven. Use it to draft policies, tests, and the workflow fast; then always run `opa eval` against at least one input that should be denied. If the output is `{}` (empty, no result) instead of a real deny, your rule never fired — the policy fails open, and this is the one gotcha the model won't warn you about. Adversarially test your own gate: ask the model to write a policy that *passes your test suite while granting a forbidden action*. If it can, your tests only cover the allow path — add the deny case and re-prove the flip.

## Connects forward

OPA plugs into the **identity-aware proxy from module 06** as an external authorization provider: Pomerium (or OAuth2-Proxy) calls OPA on every request with the JWT claims, OPA returns allow/deny on fine-grained policy. Coarse authentication stays in the proxy; fine-grained, version-controlled, tested authorization lives in OPA. The gate you built here is what keeps that policy from silently failing open in production — and feeds **module 09**, where the same access decisions become the log stream you detect on and watch for drift.

## Marketable proof

> "I write and unit-test OPA Rego policies for RBAC and Kubernetes admission, version them in git with an `opa test` CI gate, and — the part that matters — I validate the *deny* path explicitly: I can show a policy that silently fails open (the deny rule that never fires), explain why `default allow = false` plus querying the deny set makes absence fail closed, and prove my CI gate exits non-zero on the broken policy and zero on the fix."

## Stretch

- Integrate OPA with Pomerium: write a `policy.rego` that Pomerium evaluates per-request instead of YAML `allow` stanzas — the production pattern for complex authorization, tested independently of proxy config.
- Use OPA's `http.send` to fetch an external ACL (a JSON file served by a local nginx container) and evaluate access against live data rather than a bundled document — and prove the gate still fails closed when the ACL fetch *fails* (a network error must not read as "allow").
- Port one policy to **Gatekeeper** (`ConstraintTemplate` + `Constraint`) in a `kind` cluster and watch Kubernetes reject a root pod at admission time — the real enforcement point behind the `opa eval` you've been running.
