# Module 09 — Serverless Security

*Variant D · breach-driven, predict-then-reveal verdict + attacker→fixer ("the server is gone, the identity isn't"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *serverless deletes the server you patch and keeps the identity you must scope; the execution role is the whole security surface.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 02 — Cloud Identity & IAM](../02-cloud-identity-iam/README.md) · [Module 03 — IAM Attack Paths](../03-iam-attack-paths/README.md)
{ .module-meta }


## The case

In April 2022, Cado Security published the first publicly known piece of malware **built specifically
to run inside AWS Lambda.** They named it **Denonia**, after the command-and-control domain it called.
It was a Go binary wrapping the **XMRig** Monero miner, tailored to the Lambda execution environment —
it even used DNS-over-HTTPS to hide its lookups from AWS's view. The notable part isn't the miner; it's
the target. Someone wrote malware for *serverless* — the platform that was supposed to have no server to
own.

How did it get in? Not through a Lambda vulnerability. AWS [stated plainly](https://www.cadosecurity.com/blog/cado-discovers-denonia-the-first-malware-specifically-targeting-lambda)
that Denonia "does not exploit any weakness in Lambda" and "relies entirely on fraudulently obtained
account credentials." The attacker had keys, deployed (or hijacked) a function, and the function ran
their code with **whatever the execution role allowed.** No host to compromise, no patch that would have
helped. The standing power was the role.

So before you read on, this module turns on the question that separates people who *recite* "serverless
shifts risk to IAM" from people who can size the damage:

> **What is a Lambda function's blast radius — the function, or its execution role?**

## Your job

By the end of this module you'll **predict a serverless function's blast radius, then play both sides** —
enumerate a deliberately over-broad execution role and prove its reach, abuse the function across a trust
boundary with a crafted **event payload**, and then do the fixer's half: **least-privilege the role,
close the injection in the code, redeploy, and prove the path is gone.** That attacker→fixer loop, ending
in a guardrail that fails the bad role and passes the scoped one, is exactly what a cloud security
engineer is paid to deliver when a serverless workload lands on their desk.

## Call it before you read on

Don't scroll. Write down your gut answers — being wrong here is the teaching event, and you'll grade
yourself in the lab.

> **Q1.** A 40-line Lambda processes payment notifications. Its execution role has `s3:*`, `iam:*`, and
> `sts:AssumeRole` on `*`. An attacker gets code execution inside it. How far does that reach — the
> function's data, the account, or somewhere between?
>
> **Q2.** That function is tiny and runs for 200 milliseconds, then the container is gone. Doesn't its
> ephemerality *limit* the damage — there's nothing persistent to own?
>
> **Q3.** The function is triggered by an authenticated API Gateway, so the event is "trusted." Is the
> JSON payload inside that event safe to pass to a subprocess?

## The blast radius, revealed

Hold your answers against these.

**Q1 — the blast radius is the role, and the role is the account.** This is the whole module in one
line. The code is ephemeral; the **identity is standing.** When an attacker runs code inside the
function — via a poisoned dependency, a compromised deploy, or the event injection you'll do in the lab
— they don't get the function's *logic*, they get the function's *credentials*: the execution role,
fetched transparently from the Lambda environment, with no metadata-service trick required. A role with
`iam:*` lets them mint an admin user (the Denonia operator's natural next move); `s3:*` on `*` lets them
read every bucket; `sts:AssumeRole` on `*` lets them pivot. **A tiny function with an over-broad role is
a huge blast radius** — the size of the function tells you nothing; the size of the role tells you
everything. People reliably under-weight this because they look at the 40 lines and not at the policy.

**Q2 — ephemerality protects the host you no longer have, not the identity you still do.** Yes, the
container vanishes — which is exactly why there's no server to patch and no host malware to find later.
But the *power* the function wielded outlives the container: an admin user the attacker created, a role
they assumed, data they exfiltrated. Denonia's own authors leaned into this — short runtimes and
ephemeral environments make the *compromise* hard to investigate, not the *consequences* small.
**Serverless trades a persistent host you must patch for a persistent identity you must scope.** The
risk didn't shrink; it moved from the OS to the role.

**Q3 — "authenticated source" and "trusted data" are different walls.** An API Gateway that
authenticates the *caller* tells you *who* sent the event. It says nothing about what's *in* the event.
The JSON body is **untrusted input crossing a trust boundary** — the serverless analogue of an HTTP
request body, and exactly what the [OWASP Serverless Top 10](https://owasp.org/www-project-serverless-top-10/)
puts at #1 (Function Event-Data Injection). A handler that passes an event field to `subprocess`, a SQL
query, or `eval` is injectable no matter how authenticated the gateway is. Worse, when that injectable
function holds an over-broad role, it becomes a **confused deputy**: the attacker's event makes the
function take actions *with the function's privileges* that the attacker could never take directly. The
event boundary and the role are two halves of the same surface — that's why you fix both in the lab.

The bridge to keep: **serverless doesn't remove the attack surface, it relocates it into the execution
role and the event boundary.** There's no host to harden, so the entire job is (1) scope the role to the
minimum the function actually needs, and (2) treat every event field as hostile input. The lab makes you
do both, then encodes the role half as a check that can't silently regress.

## Learn (~3.5 hrs)

*A specialist module — it curates more than a foundations one. You already own the IAM evaluation model
from modules 02–03; here you apply it to the serverless shape. Read the case first.*

**The serverless attack surface (~1.5 hrs)**
- [OWASP Serverless Top 10](https://owasp.org/www-project-serverless-top-10/) (~40 min) — the canonical reference. Read all ten; #1 Event-Data Injection and the over-privileged-function items are the spine of this lab. Note how many map to "the role" or "the event," the two surfaces from the reveal.
- [Cado Security — *Cado Discovers Denonia: The First Malware Specifically Targeting Lambda*](https://www.cadosecurity.com/blog/cado-discovers-denonia-the-first-malware-specifically-targeting-lambda) (~25 min) — the primary writeup of the anchor. Read for *how it got in* (stolen creds, not a Lambda CVE) and why ephemerality aids the attacker, not the defender.
- [AWS — official statement quoted in the Cado writeup](https://www.cadosecurity.com/blog/cado-discovers-denonia-the-first-malware-specifically-targeting-lambda) (in the same post) — "relies entirely on fraudulently obtained account credentials." This is the shared-responsibility verdict from module 01, restated for serverless.

**The standing power — execution roles (~1 hr)**
- [AWS Lambda — security best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (~25 min) — read the *execution role least privilege* and *environment variable* sections; this is the official statement of the fix you'll author.
- [BishopFox — cloudfox README (AWS, `permissions` + `role-trusts`)](https://github.com/BishopFox/cloudfox) (~20 min) — the enumeration accelerator; skim so the lab's "what can this role reach" step is familiar. (You used it in module 03 against IAM graphs — same tool, pointed at a Lambda role.)

**Deploy & exploit tooling (~1 hr)**
- [AWS SAM CLI — what it is, and `sam deploy`](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-deploy.html) (~20 min, skim) — the deploy tool the lab uses; you only need the deploy/redeploy flow.
- [Pacu — RhinoSecurityLabs/pacu, the Lambda module list](https://github.com/RhinoSecurityLabs/pacu) (~20 min, orient) — read which Lambda modules exist; you won't drive Pacu here, but it shows how a real operator automates the privesc your cloudfox finding exposes (and you'll use it in module 14).

## Key concepts
- A serverless function's blast radius is its **execution role**, not its code size — a tiny function with `iam:*`/`s3:*` on `*` is an account-wide blast radius
- Code is ephemeral; **identity is standing** — the container vanishes but the admin user / assumed role / exfiltrated data the role enabled does not
- Event data is **untrusted input crossing a trust boundary** — an authenticated *source* does not make the payload safe (OWASP Serverless #1)
- Injectable function + over-broad role = **confused deputy**: the attacker's event makes the function act with privileges the attacker lacks
- Denonia got in via stolen credentials, *not* a Lambda CVE — the provider owns the runtime; the customer owns the role and the input handling
- The fix has two halves and both are verifiable: scope the role to the minimum (prove with `simulate-principal-policy`), and allowlist/validate event fields in code

## AI acceleration
`cloudfox` and `aws iam get-role-policy` emit structured JSON — strong AI input. Hand a model the
execution role's policy and ask it to chart the highest-impact path from "code execution in the function"
to "account compromise," step by step with the IAM action and ATT&CK technique for each. It's good at
that graph-traversal narration. What it can't do for you: confirm the path is *actually* reachable (an
SCP or permission boundary may cap the policy text — validate with `simulate-principal-policy`), and
write the **minimum** role that still lets the function do its real job. That least-privilege cut is the
judgment the module is about: AI drafts the policy and the guardrail; you prove the dangerous reach is
denied and the legitimate call still works, and you own the verdict.
