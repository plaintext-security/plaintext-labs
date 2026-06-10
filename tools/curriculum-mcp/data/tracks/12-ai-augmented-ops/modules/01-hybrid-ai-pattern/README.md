# Module 01 — The Hybrid AI Pattern

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *not every task needs a frontier model — the decision of what runs where is itself a security posture.*

## Why this matters
Security teams are under constant pressure to do more with less. AI promises relief, but naively
reaching for a cloud model on every task creates new problems: sensitive alert data leaving the
perimeter, unpredictable latency when a triage queue is growing, and a hard dependency on a vendor
API being reachable during an incident. Getting the routing right — what stays local, what goes to a
frontier model, what stays human — is one of the first architectural decisions in building AI-augmented
security operations.

## Objective
Build a practical decision framework for AI task routing in a security context and validate it
against representative workloads. Articulate — in writing — why a given task goes local, frontier,
or human-only.

## The core idea
Think of AI models on a spectrum from "small and local" to "large and remote." A small local model
(7B parameters, running on commodity hardware via Ollama) is like a competent first-tier analyst
who works fast, never sleeps, and never sends your data anywhere — but whose reasoning ceiling is
lower and whose domain knowledge stops at training cutoff. A frontier model (GPT-4o, Claude Sonnet)
is like a brilliant outside consultant: better reasoning, broader knowledge, but expensive, rate-limited,
and every call is a data transfer out of your control. **The job isn't picking one; it's routing
intelligently across both — and knowing when neither is the right answer.**

The routing logic isn't complicated, but it has to be *explicit*. Three axes drive the decision:
**sensitivity** (would you print this alert and hand it to a contractor?), **latency tolerance**
(does the analyst wait seconds or can they wait minutes?), and **reasoning complexity** (is this a
pattern-match on known signatures, or does it require cross-domain synthesis?). Alert triage on
internal logs is high-sensitivity, low-latency, medium-complexity — local wins. Writing a post-incident
executive summary is medium-sensitivity (scrubbed), high-latency-ok, high-complexity — frontier earns
its cost. Advising on whether to pay a ransom demand is low-sensitivity-data but maximal-stakes
reasoning — that's a human decision, and a model's role is to prepare briefing material, not decide.

A subtler point: **model confidence is not accuracy.** Both local and frontier models will
hallucinate — small ones more frequently, large ones more convincingly. In a security context, a
hallucinated CVE ID or a fabricated IOC can send an investigation off a cliff. The hybrid pattern
isn't just about data sensitivity; it's about recognizing that the output of any model is a *draft
for review*, not an authoritative answer. The distinction between tasks where a wrong answer is
recoverable (suggest a search query, draft a report) versus irrecoverable (trigger a containment
action, write a firewall rule to prod) is the most important line in your routing table.

The Meridian Financial security team learned this concretely during their first proof-of-concept:
they ran alert classification through a hosted model, got excellent accuracy, and shipped it —
then discovered three months later that alert payloads containing internal hostnames and usernames
had been sent to a third-party API under a terms-of-service that permitted model training on inputs.
The data wasn't exfiltrated in an adversarial sense, but it left the boundary in a way their data
classification policy didn't permit. Local-first is a compliance posture, not just a latency choice.

## Learn (~3 hrs)

**Foundations of LLM deployment (~1.5 hrs)**
- [Ollama — run LLMs locally](https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image) — the Docker image doc; skim to understand how the serving layer works before you touch it in the lab.
- [Andrej Karpathy, "Intro to Large Language Models" (YouTube, 1 hr)](https://www.youtube.com/watch?v=zjkBMFhNj_g) — the best non-mathy explanation of what a model actually does; the section on "LLM OS" framing (40:00–60:00) maps directly to the hybrid pattern.

**Routing and risk framing (~1 hr)**
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — LLM06 (Sensitive Information Disclosure) and LLM09 (Overreliance) are the two risks the routing table directly manages; read the descriptions and example scenarios.
- [NIST AI Risk Management Framework (AI RMF) — Govern function overview](https://airc.nist.gov/) — one page: what "govern" means for AI deployment. Understand the MAP category before you write your decision matrix.

**Practitioner view (~30 min)**
- [Simon Willison, "Things we learned about LLMs in 2024"](https://simonwillison.net/2024/Dec/31/llms-in-2024/) — dense practical survey from one of the clearest thinkers on operational LLM use; skim for the sections on local models and privacy.

## Key concepts
- Local vs. frontier vs. human-only routing — three axes: sensitivity, latency, reasoning complexity
- Model confidence ≠ accuracy: every output is a draft for review
- Recoverable vs. irrecoverable consequences as a routing gate
- Data residency as a compliance constraint, not just a latency choice
- The "AI authors → you review → you own it" posture applied to task routing

## AI acceleration
Have a model help you fill in your decision matrix — give it the three axes and ask it to reason
through a new task category. Then review each cell: the model doesn't know your data classification
policy, your incident response SLAs, or your vendor contracts. It drafts the structure; you supply
the real constraints and own the resulting policy.
