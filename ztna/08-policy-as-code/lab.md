# Lab 08 — Encode the Verdict as a Gate: policy that fails closed

> **Hands-on lab.** Environment: `plaintext-labs/ztna/08-policy-as-code`.
> Objective: **write real OPA/Rego policy, prove the deny path fires, and leave behind a CI gate that
> exits non-zero on a fail-open policy and zero on the fix.**
> Target: **~90 min**, one finish line. This is a **reference lab — real `opa` in a container, no mocks.**

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **OPA is a decision point, not the enforcer.** PEP calls PDP; your code acts on the answer. | Policy is separable from the stack → testable in ms → gate-able in CI. |
| 2 | **Rego is declarative — a rule whose condition is never true is *silently absent*.** | No error. The `deny` you "wrote" may deny nothing. |
| 3 | **A deny that never fires defaults to allow → fail open.** | This is the whole module. Run the must-deny case and confirm it *fired*. |
| 4 | **`default allow := false` + query the deny decision = absence fails *closed*.** | Structure, not vigilance, is what makes "no rule fired" mean *reject*. |
| 5 | **K8s: deny explicit `runAsUser: 0` AND omitted `runAsUser`** (root by default). | The omitted-field case is the one AI drafts almost always miss. |
| 6 | **The gate is the deliverable:** non-zero on broken, zero on fixed. | A test that only proves the allow path is theater; the flip is the proof. |

*(If you can explain all six cold at the end — especially #2 and #3 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [centerpiece section](README.md#the-centerpiece-a-rule-that-never-fires-is-silently-absent) and
> [the gate is the deliverable](README.md#the-gate-is-the-deliverable).

---

## Warm-up — answer before you touch the container (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. You wrote a `deny` rule but typo'd the claim — you check `input.user.roles` (plural) when the request
   spells it `input.user.role`. You query `data.corp.access.deny` for the request that must be blocked.
   What value comes back — and what happens if your enforcer treats "not denied" as "allow"?
2. A pod spec omits `runAsUser` entirely — no `securityContext.runAsUser` at all. Is that pod root?
   Should your policy deny it? Why do AI-drafted admission policies usually let it through?

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. The container bundles the
**real `opa` binary** (pinned `openpolicyagent/opa:0.68.0`); every target runs real Rego evaluation.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/08-policy-as-code
make up        # start the OPA container (real opa, pinned)
make demo      # run both scenarios — allow + deny cases for each
make test      # opa test over every policy in data/policies/ (-v)
make eval POLICY=<path> INPUT=<path>   # one-off: eval a policy against an input
make shell     # OPA REPL loaded with the lab policies (distroless — no shell, the REPL is the surface)
make down      # stop it when you're done
```

> **▸ On track if:** `make demo` prints the two scenario banners and, for each case, a JSON block whose
> `"value"` matches the label — e.g. Case A analyst READ shows `"value": true` for
> `data.corp.access.allow`; Case B analyst WRITE shows `"value": false` for `allow` **and**
> `"value": true` for `data.corp.access.deny`. The policies you edit live in `data/policies/`; the
> requests in `data/inputs/`.

> **Authorization note.** Everything runs locally against bundled data you own — no external targets, no
> authorization needed. (The Rego you write here can later gate a *real* proxy or cluster; there the rule
> binds — only enforce against systems you own or have explicit written permission to test.)

---

## Build it — read a little, do a little

### Step 1 — Read the policy, predict, then run both scenarios

**Concept (30 sec):** Flight-card #1. OPA answers; it doesn't enforce. `make demo` feeds four data-access
requests and three pod specs through real `opa eval` and prints each decision. Predicting *before*
running is how you find out whether you actually understand the rules.

**Do it:** open `data/policies/data-access.rego` — find `default allow := false`, the three `allow`
rules (analyst-read, admin-any, service_account-read), and the two `deny` rules (analyst-write,
service_account-write). Read the four `data/inputs/*.json` and **predict** each verdict. Then read
`data/policies/k8s-admission.rego` and its three pod inputs. Run `make demo`.

> **▸ On track if:** your predictions match the output — analyst READ → `allow: true`; analyst WRITE →
> `allow: false`, `deny: true`; admin WRITE → `allow: true`; service_account WRITE → `allow: false`,
> `deny: true`; pod-root and pod-no-user → `deny: true`; pod-nonroot → `deny: false`. Where deny
> overrides allow (analyst write), confirm the **deny** query returned `true` — not merely that allow
> was false.

### Step 2 — Add an `auditor` role with a deny the others don't have

**Concept (30 sec):** Flight-card #2. Compliance wants an `auditor` who can **read** but can **never**
hit `/export` (bulk download), regardless of action. That's an allow rule *and* a deny rule that
overrides it — the exact shape where a silently-absent deny hurts.

**Do it:** in `data-access.rego`, uncomment/complete the lab-exercise block so `auditor` gets an
`allow` (read) and a `deny` on `resource == "/export"`. Create `data/inputs/auditor-export.json`
(`role: auditor`, `action: read`, `resource: /export`). Confirm the denial:

```bash
make eval POLICY=data/policies/data-access.rego INPUT=data/inputs/auditor-export.json
```

> **▸ On track if:** the emitted `data` document shows `corp.access.deny` as `true` for the
> auditor-export request (allow may also be `true` — that's the point of *deny overrides allow*). If
> `deny` is `false`, your rule isn't firing — check the claim name and the `/export` string exactly.

### Step 3 — The fail-open trap: plant it, watch the deny vanish, catch it

**Concept (30 sec):** Flight-card #3 — the centerpiece. A `deny` whose condition is never true isn't an
error; it's a rule that quietly isn't there, and the default takes over.

**Do it:** break your new auditor/`/export` deny in one realistic way — typo the claim
(`input.user.roles`), flip the comparison (`!=` where you meant `==`), or guard it behind a field the
input never carries. Re-run the exact `make eval` from step 2. **The denial disappears.** Record the
one line you saw in `fail-open-proof.md`. Then restore the correct rule and confirm the deny is back.

> **▸ On track if:** with the bug planted, `corp.access.deny` for auditor-export drops to `false` (the
> rule never fired, the default applied) — and `default allow := false` + querying the **deny** decision
> is what makes that absence resolve to *reject* in your enforcer, not *allow*. Broken → open, fixed →
> closed: that pair **is** the lesson, not the syntax.

!!! warning "This is the one that ships breaches"
    A green demo with a silently-absent deny is *exactly* how Broken Access Control (OWASP A01) reaches
    production. The policy looks complete; the hole is the rule you meant to write. The only defense is
    running the must-deny case and confirming it fired — which is what step 4 makes automatic.

### Step 4 — Make the deny path a *test* (so the trap can't come back)

**Concept (30 sec):** Flight-card #6. A discipline you have to remember is a discipline you'll forget.
`opa test` turns "run the deny case" into a unit test that a machine runs on every change.

**Do it:** in `data/policies/data-access_test.rego`, uncomment the `auditor` tests and confirm you have
at least `test_analyst_write_denied`, `test_auditor_export_denied`, and `test_analyst_read_allowed`. Run
`make test`. Then **re-plant the step-3 bug** and run `make test` again — the deny test must now go red.
Fix the policy, confirm green, keep this proof.

> **▸ On track if:** `make test` prints `PASS` for every `test_` rule (data-access + k8s-admission,
> summary `PASS: N/N`) with the policy correct — and with the bug re-planted, `test_auditor_export_denied`
> flips to **FAIL**. A suite that stays all-green while the deny rule is broken is testing nothing.

### Step 5 — K8s admission: the omitted-field trap, and an AI-drafted policy you must break-test

**Concept (30 sec):** Flight-card #5. "No root pods" means two cases: explicit `runAsUser: 0` **and** an
*omitted* `runAsUser` (root by default). AI writes the first and forgets the second — the same fail-open
trap wearing a Kubernetes costume.

**Do it:** confirm `k8s-admission.rego` denies both — `make eval` on `pod-root.json` and
`pod-no-user.json` (both `deny: true`), and `pod-nonroot.json` (`deny: false`). Then run the
AI-drafting exercise: ask a model for *"an OPA Rego policy that denies pods that don't set
`readOnlyRootFilesystem: true`"*, save it as `data/policies/readonly-fs.rego`. **Before trusting it**,
write `data/inputs/pod-writable-fs.json` (the case that must be denied) and a deny test in
`data/policies/readonly-fs_test.rego`. Run `make test`.

> **▸ On track if:** `pod-no-user.json` returns `deny: true` (if it doesn't, the policy missed the
> omitted-field case — fix it); and your `readonly-fs` deny test either passes, or fails and *exposes*
> that the AI wrote only the allow path — in which case you close the hole yourself and re-prove green.

---

## Prove the control (your finish line)

One assertion is the whole module: **the gate flips.** Add a `make ci` gate (the repo ships one — `opa
test ./data/policies/`) and a GitHub Actions workflow `.github/workflows/opa-test.yml` (on `push` +
`pull_request`) that runs it. Have a model draft the workflow; **read every line** and confirm its `opa
test` invocation matches what you run locally.

**The proof — run it both ways:**

```bash
# 1) with a fail-open bug planted (re-break the auditor/export deny):
make ci ; echo "exit: $?"     # → tests fail, exit NON-ZERO

# 2) restore the fix:
make ci ; echo "exit: $?"     # → all tests pass, exit ZERO
```

Capture both `exit:` lines into `fail-open-proof.md`. *A gate whose exit code doesn't change between
broken and fixed isn't a gate — it's a report.* That single flip, allow proven **and** deny proven, is
what makes the policy a control instead of a hope.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why can you unit-test an OPA policy in milliseconds without standing up a proxy or a cluster?
2. You query `deny` for a request that should be blocked and get `false`. Name two distinct reasons the
   rule might not have fired — and why `default allow := false` alone doesn't save you.
3. Name the two pod cases the admission policy must both deny, and say which one AI usually misses.

Missed one? Re-run the step that built it, or pull the [module centerpiece](README.md#the-centerpiece-a-rule-that-never-fires-is-silently-absent) — then re-answer.

---

## Deliverables

Commit to your portfolio repo:

- **`data/policies/data-access.rego`** — extended with the `auditor` read-allow + `/export` deny, structured to fail closed (`default allow := false`).
- **`data/policies/data-access_test.rego`** — the suite including the explicit deny-path cases (`test_auditor_export_denied`).
- **`data/policies/readonly-fs.rego` + `readonly-fs_test.rego`** — the AI-drafted policy with *your* deny-path test.
- **`data/inputs/auditor-export.json`** and **`data/inputs/pod-writable-fs.json`** — the new inputs.
- **`fail-open-proof.md`** — the one-line record from step 3 (what the broken deny produced) plus the two `exit:` captures from the finish line (broken vs. fixed) proving the gate flips.
- **`.github/workflows/opa-test.yml`** — the CI gate.

Do **not** commit raw `opa eval` JSON dumps, or the `data/` files seeded by the lab that you didn't
change. The `git history` is the audit trail for who changed which policy and when — that is
policy-as-code's whole point.

## Automate & own it

**Required — this is the judgment-as-code core of the module.** The policy tests **are** the automation.
Your verdict is: *"these access rules must hold, and a deny rule that silently fails open must never pass
review."* Encode it as a portable gate — `gate.sh`, one script that:

1. runs `opa test ./data/policies/` (exit non-zero on any failing/erroring test), and
2. runs `opa eval` on each must-deny input and **asserts the deny actually fired** (`deny == true`, not
   an empty/`false` result) — so a silently-absent deny fails the gate instead of sliding through, and
3. prints which policy/input combination blocked it.

Then prove the harness: with a fail-open bug planted `gate.sh` exits 1; with it fixed it exits 0; assert
the flip. **Have a model draft the bash and the `jq`/`opa eval` checks; review every line** — confirm an
`opa` *error* doesn't read as a *clean pass*, and that the gate fails for the *right* reason (the missing
deny), not an unrelated parse nit. This gate is your verdict made un-recurrable.

## Definition of done (`policy-as-code` ✅)

- [ ] `make demo` shows every labelled allow/deny case for both scenarios, and you confirmed each deny *fired* (not merely that allow was absent).
- [ ] The `auditor` role is denied on `/export`, with an input and a passing `opa test` case covering it.
- [ ] You **caught a fail-open gap**: planted a silently-absent deny, watched `deny` drop to `false`, and can explain why `default allow := false` + querying the deny decision makes absence fail *closed*.
- [ ] `make test` is green; re-planting the deny bug turns `test_auditor_export_denied` **FAIL** (the test genuinely exercises the deny path).
- [ ] The K8s policy denies **both** explicit-root and omitted-`runAsUser` pods; the AI-drafted `readonly-fs` policy has a passing deny-path test.
- [ ] The gate exits **non-zero on the broken (fail-open) policy and zero on the fix** — captured with `$?`. You can explain all six flight-card facts cold.

## Connects forward

OPA plugs into the **identity-aware proxy from Module 06** as an external authorization provider:
Pomerium (or OAuth2-Proxy) calls OPA on every request with the JWT claims, OPA returns allow/deny on
fine-grained policy. Coarse authentication stays in the proxy; fine-grained, version-controlled, tested
authorization lives in OPA. The gate you built here keeps that policy from silently failing open in
production — and feeds **Module 09**, where the same access decisions become the log stream you detect
on and watch for drift.

## Marketable proof

> "I write and unit-test OPA Rego policies for RBAC and Kubernetes admission, version them in git with
> an `opa test` CI gate, and — the part that matters — I validate the *deny* path explicitly: I can show
> a policy that silently fails open (the deny rule that never fires), explain why `default allow := false`
> plus querying the deny decision makes absence fail closed, and prove my CI gate exits non-zero on the
> broken policy and zero on the fix."

## Stretch

- Integrate OPA with Pomerium: write a `policy.rego` that Pomerium evaluates per-request instead of YAML `allow` stanzas — the production pattern for complex authorization, tested independently of proxy config.
- Convert `deny` from a boolean to a **partial set of reason strings** (`deny contains msg if { … }`) so a rejection tells the developer *why* — then confirm your gate still catches a member that's never added (a reason you never emit = a deny that never fired).
- Use OPA's `http.send` to fetch an external ACL (a JSON file served by a local nginx container) and evaluate against live data — then prove the gate still fails **closed** when the ACL fetch *errors* (a network failure must not read as "allow").
- Port one policy to **Gatekeeper** (`ConstraintTemplate` + `Constraint`) in a `kind` cluster and watch Kubernetes reject a root pod at admission time — the real enforcement point behind the `opa eval` you've been running.
