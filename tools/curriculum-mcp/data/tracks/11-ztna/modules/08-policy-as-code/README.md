# Module 08 — Policy as Code

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *authorization logic that lives in git, gets reviewed, and can be tested like software.*

## Why this matters

When access policy lives in a UI — a checkbox in your IdP, a firewall rule buried in a vendor portal — it drifts. The person who enabled the exception three years ago is gone. The audit log says the rule changed but not why. The quarterly access review catches it eventually, maybe. Policy as code puts the same authorization logic in a version-controlled file, surrounded by tests, deployed through a pull request, and auditable as a git blame. The same engineering practices that keep application code from regressing keep your policy from drifting.

In a Zero Trust architecture this matters more than in a perimeter model because ZT moves authorization decisions from "is this traffic inside the network?" to "does this specific identity, at this specific time, with this specific device posture, have permission to do this specific thing?" That is a complex predicate. You cannot express it reliably in a UI. You need a language designed for authorization logic and a runtime that evaluates it consistently at scale.

## Objective

Write and evaluate two Rego policies with OPA: one that gates data access by user role (analyst can read, cannot write), and one Kubernetes admission policy that rejects pods running as root. Demonstrate both allow and deny cases and show how AI drafts policy while you own the deny-path validation.

## The core idea

Open Policy Agent is a general-purpose policy engine: you describe your authorization logic in **Rego** (a declarative query language purpose-built for policy), feed it a JSON document representing the request (`input`), and OPA evaluates whether the policy allows or denies it. The key design insight is that OPA is *decoupled* from enforcement — it does not sit in the data path. Instead, your application (or your Kubernetes admission webhook, or your Envoy proxy) calls OPA as a sidecar or service, gets a structured decision back (`{"allow": true}` or `{"allow": false, "reason": "..."}`), and enforces it. The policy logic and the enforcement point are separate, which means you can test the policy without spinning up the full application stack.

Rego is worth a moment of investment because it looks unfamiliar at first. It is a logic programming language, not an imperative one — you write what must be true for `allow` to be true, not a sequence of if-statements. A `deny` rule that is never satisfied is silently absent, which is the source of the most dangerous class of mistake in OPA: writing a `deny` rule that you think covers a case, but because a condition in it is never true, the default — no deny rule fired — applies, and access is granted. This is why you must always test the deny path explicitly.

The Kubernetes admission use case illustrates the operational leverage. Rather than relying on every developer to remember "never run containers as root" and every reviewer to catch it in a PR, you express the rule once in Rego, register OPA as a validating admission webhook, and Kubernetes enforces it automatically on every pod create or update. The policy is code; the cluster is the test harness. AI will draft this Rego for you in seconds — the question is whether you tested the case where a pod declares `runAsUser: 0` in the securityContext, and the case where it omits `runAsUser` entirely (which is also effectively root by default).

Data access policy in Rego follows the same shape. You write `allow if input.user.role == "analyst"` and `deny if input.action == "write"` (where `deny` overrides `allow` by convention). The real-world version reads groups from a JWT claim, cross-references an external data document (`data.acl`) that maps groups to permissions, and applies time-of-day or device-posture conditions from context. Rego handles all of that; the lab gives you the minimal version to build the mental model before layering in the full context.

## Learn (~3 hrs)

**OPA and Rego foundations (~1.5 hrs)**
- [OPA: The Basics (official interactive tutorial)](https://www.openpolicyagent.org/docs/policy-language) — the canonical introduction to Rego; work through the "Imports," "Rules," and "Comprehensions" sections. The interactive playground in the sidebar lets you run examples without installing anything.
- [Rego Language Reference (official docs)](https://www.openpolicyagent.org/docs/latest/policy-language/) — comprehensive Rego syntax and built-in functions reference; use as a quick lookup during the lab's policy-writing steps.

**OPA in Kubernetes admission (~45 min)**
- [OPA Gatekeeper: Introduction (official docs)](https://open-policy-agent.github.io/gatekeeper/website/docs/) — Gatekeeper is the production path for OPA admission in Kubernetes (wraps OPA with CRDs); read the architecture overview and the "Constraints" section. The lab uses raw OPA `eval` for simplicity, but Gatekeeper is what you'd use in production.

**Policy as code practices (~45 min)**
- [Policy-as-Code Principles (NIST and IETF guidance)](https://www.ietf.org/rfc/rfc7232.txt) — the conceptual argument for treating policy as version-controlled infrastructure; read alongside the OPA docs for the "why" behind PAC.
- [OPA Testing Guide (official docs)](https://www.openpolicyagent.org/docs/policy-testing) — `opa test` lets you write unit tests for Rego policies the same way you'd test application code. Essential for the "deny path explicitly tested" requirement.

## Key concepts
- OPA is a policy engine, not an enforcement point — it returns decisions; your infrastructure enforces them.
- Rego is declarative: you write what must be true for `allow`, not a sequence of if-statements.
- A `deny` rule that never fires is silently absent — the default is allow. Always test the deny path.
- Kubernetes admission webhooks use OPA (via Gatekeeper) to reject non-compliant pods at create time.
- Policy as code = version control + PR review + CI tests + audit trail.
- AI drafts Rego well; you validate it by running the deny cases yourself.

## AI acceleration

AI generates Rego quickly and accurately for common patterns (role-based access, resource constraints, Kubernetes pod security). The non-negotiable follow-up: run `opa eval` against an input that should be denied and confirm you get `{"allow": false}` — not `{}` (empty result, which OPA returns when no rule fires, which defaults to deny only if your evaluation query is structured correctly). The failure mode is a policy that "passes" because nobody checked whether the rule was ever evaluated at all.
