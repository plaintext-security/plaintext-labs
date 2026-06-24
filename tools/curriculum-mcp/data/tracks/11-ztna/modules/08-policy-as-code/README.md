# Module 08 — Policy as Code

*Type 8 · Judgment-as-Code / Gate — the deliverable is a policy gate that fails-bad and passes-good in CI; you prove it both ways and catch a fail-open gap. (Secondary: Build-&-Operate — you run real OPA over real Rego.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *authorization logic that lives in git, gets reviewed, gets tested like software — and fails closed when you forget a rule.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · Module 06 (Identity-Aware Access) for the OIDC/JWT claims a policy reads
{ .module-meta }

## Why this matters

When access policy lives in a UI — a checkbox in your IdP, a firewall rule buried in a vendor portal — it drifts. The person who enabled the exception three years ago is gone. The audit log says the rule changed but not why. The quarterly access review catches it eventually, maybe. Policy as code puts the same authorization logic in a version-controlled file, surrounded by tests, deployed through a pull request, and auditable as a `git blame`. The same engineering practices that keep application code from regressing keep your policy from drifting.

In a Zero Trust architecture this matters more than in a perimeter model, because ZT moves authorization from "is this traffic inside the network?" to "does *this* identity, at *this* time, with *this* device posture, have permission to do *this* thing?" That is a complex predicate — too complex to express reliably in a UI. You need a language built for authorization logic and a runtime that evaluates it consistently at scale. But the same expressiveness hides the failure mode this module is built around: **a rule you never wrote is an allow.** A policy that fails *open* is worse than no policy, because it looks like a control while granting everything. The deliverable here is a gate that catches that.

## The core idea: the gate is the deliverable, and the dangerous default is *allow*

Open Policy Agent is a general-purpose policy engine. You describe your authorization logic in **Rego** (a declarative, logic-programming query language built for policy), feed it a JSON document representing the request (`input`), and OPA returns a structured decision — `{"allow": true}` or `{"deny": ["pod runs as root"]}` — which *your* infrastructure then enforces. The design insight is that OPA is **decoupled from enforcement**: it doesn't sit in the data path. Your app, your Kubernetes admission webhook, or your identity-aware proxy (module 06) *calls* OPA and acts on the answer. Because the policy and the enforcement point are separate, you can test the policy in milliseconds without standing up the whole stack — which is precisely what makes it gate-able in CI. **That gate is the deliverable of this module:** the verdict encoded so it can't regress when someone copies the policy next quarter.

Now the centerpiece gotcha, and the reason this is a *judgment-as-code* module and not a "learn Rego" page. Rego is declarative: you write *what must be true* for a rule to fire, not a sequence of if-statements. A rule that is never satisfied is not an error — it is **silently absent**. So if you write a `deny` rule but a condition inside it is never true (a typo'd field, a `==` that should be `!=`, an `input.user.role` that the request actually spells `input.user.roles`), the rule simply never fires, *no deny is produced, and the default applies.* If your evaluation is structured so that "no deny" means "allow," you have just shipped a policy that **fails open**: it denies nothing, passes every test you only wrote for the allow path, and grants access to exactly the case you thought you'd blocked. This is the single most dangerous class of OPA mistake, and the worst part is that it is invisible — the policy looks complete, the demo is green, and the hole is the rule you *meant* to write. **The skill is testing the deny path explicitly, and structuring the query so absence-of-decision means deny, not allow.**

A scanner — or OPA itself — is a fast junior reviewer with no context: it evaluates exactly the rules you wrote, instantly, every time, and tells you *nothing* about the rule you forgot. That blind spot is where you add the value the tool can't. So the lab's rhythm is: write the policy → run the case that *must* be denied → confirm you got `{"deny": [...]}` and not `{}` (empty — no rule fired) → wire it into a gate that exits non-zero on the bad input and zero on the good one. The two scenarios — **role-based data access** (analyst reads, can't write; deny overrides allow) and **Kubernetes admission** (reject any pod running as root, including the one that *omits* `runAsUser`, which is also root by default) — are deliberately small so the mechanism is legible. AI will draft both Rego files in seconds and they will look correct; the question that separates a control from a liability is whether *you* ran the deny case and proved the gate flips.

## Learn (~3 hrs)

*Build-first and tool-heavy: read enough to write a real policy, test its deny path, and wrap it in a gate — then go to the lab.*

**OPA and Rego foundations (~1.25 hrs)**
- [OPA — Policy Language (official docs)](https://www.openpolicyagent.org/docs/policy-language) (~50 min) — the canonical Rego reference. Read **Rules**, **The `default` keyword**, and **Negation** carefully: `default` is your fail-closed switch, and negation is where "the rule never fired" silently becomes an allow. Skim Comprehensions; you'll use them but the lab's policies are deliberately simple.
- [OPA — Policy Testing (official docs)](https://www.openpolicyagent.org/docs/policy-testing) (~35 min) — `opa test` lets you unit-test Rego the way you test application code: `test_` functions, the `with ... as ...` input-mocking keyword, and `--coverage`. This is the tool that makes "explicitly test the deny path" mechanical rather than a discipline you have to remember.

**OPA in Kubernetes admission (~45 min)**
- [OPA Gatekeeper — Introduction (official docs)](https://open-policy-agent.github.io/gatekeeper/website/docs/) (~45 min) — Gatekeeper is the production path for OPA admission in Kubernetes (it wraps OPA in CRDs: `ConstraintTemplate` + `Constraint`). Read the admission-webhook architecture and the **Constraints** model. The lab uses raw `opa eval` for legibility, but read this so you know what the real deployment looks like.

**Policy as code as a gate (~1 hr)**
- [OPA — CLI reference: `opa eval` / `opa test` exit codes](https://www.openpolicyagent.org/docs/cli/) (~25 min) — the gate lives or dies on exit codes. Read exactly when `opa test` exits non-zero, and how `opa eval --fail` / `--fail-defined` turn a decision into a process exit you can gate on in CI (`--fail` exits non-zero on an *undefined/empty* result; `--fail-defined` exits non-zero on a *defined* one — pick the one that makes "the bad state" non-zero).
- [The Rego Playground](https://play.openpolicyagent.org/) (~15 min) — paste a policy + input and watch the decision in the browser; the fastest way to *see* a deny rule silently not firing (the output is `{}`, not `false`) before you've installed anything.
- [CNCF / OPA — "Policy-based control for cloud native environments" (project overview)](https://www.cncf.io/projects/open-policy-agent-opa/) (~20 min) — the "why" behind treating authorization as version-controlled, testable infrastructure rather than scattered per-app checks; ZTNA's per-request authorization is exactly this pattern (OPA is a CNCF *graduated* project).

## Key concepts
- OPA is a policy engine, not an enforcement point — it returns a decision; your proxy / admission webhook / app enforces it. Decoupling is what makes the policy testable and gate-able.
- Rego is declarative: you write *what must be true* for a rule to fire, not control flow. A rule whose condition is never true is **silently absent** — no error, no decision.
- **The fail-open trap is the whole module:** the `deny` rule you forgot to write (or that never fires) defaults to *allow*. Always test the deny path, and structure the query so "no decision" means deny.
- `default allow = false` (and asking the deny set, not the allow flag) is how you make absence-of-rule fail *closed*.
- Kubernetes admission must cover **both** explicit `runAsUser: 0` **and** an omitted `runAsUser` — the second is also root, and is the case AI drafts most often miss.
- The deliverable is the **gate**: it exits non-zero on the bad input and zero on the fixed one, so the verdict can't regress. A test that only checks the allow path is not a gate; it's theater.
- Policy as code = version control + PR review + `opa test` in CI + a `git blame` audit trail.

## AI acceleration

AI is fluent at Rego for common patterns — RBAC, Kubernetes pod security, JWT claim checks — and will draft both of this lab's policies correctly-looking in seconds. That fluency is exactly the hazard, because the model writes the *allow* path it was asked for and rarely the *deny* path you actually need proven. The non-negotiable follow-up after every AI-drafted policy: run `opa eval` against an input that **must** be denied and confirm you get `{"deny": [...]}` (or `{"allow": false}` for an allow-shaped query) — **not** `{}`. An empty result means no rule fired, which in a poorly-structured query reads as allow: the policy "passes" because nobody checked whether the rule was evaluated at all. The model will not warn you about this; it is the one thing you own. Make AI draft the policy, the tests, and the CI workflow; **you** write the deny-case input, confirm the gate fails the bad state for the *right* reason, and confirm it passes only the genuine fix. AI authors, you review every line, you own the verdict — and you own the rule it forgot to write.
