# Lab 01 — The Hybrid AI Pattern

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/01-hybrid-ai-pattern
make up && make demo
```

**Requirements:** Docker, 4 GB RAM free. No GPU needed — `tinyllama` runs on CPU.
The first `make up` pulls the Ollama image (~1 GB) and the `tinyllama` model (~637 MB).
Subsequent runs use the cache.

## Scenario
Meridian Financial's security team has approved a pilot: use local AI to pre-triage a queue of
alerts before a human analyst reviews them. Before writing any code, your job is to build the
routing decision matrix — what runs locally, what (if anything) goes to a frontier model, and what
stays human-only — and validate the framework against live model output.

> Everything in this lab runs against local infrastructure you own. No external targets, no
> authorization concerns.

## Do

1. [ ] `make demo` and read the output. The demo asks `tinyllama` a single security question and
   displays the latency and token throughput. Note the quality of the answer. Is it accurate? Is
   there anything you'd be uncomfortable acting on without review?

2. [ ] Open `data/decision-matrix.md`. Read the three routing axes (sensitivity, latency tolerance,
   reasoning complexity) and the example task classifications. For each of the five blank task rows
   at the bottom, fill in your routing decision (Local / Frontier / Human) and a one-sentence
   rationale.

3. [ ] `make shell` and run the Ollama API directly:
   ```bash
   curl -s http://localhost:11434/api/generate \
     -d '{"model":"tinyllama","prompt":"Summarize CVE-2021-44228 in one sentence.","stream":false}' \
     | python3 -m json.tool
   ```
   Compare the quality of the summary to the NVD entry. Where does the model get it right?
   Where does it drift?

4. [ ] Now stress-test your routing matrix. Pick the two tasks you marked "Local" in step 2 and
   run them through the model (`make shell`, then craft prompts). Do the answers meet the
   threshold you'd accept from a first-tier analyst? Adjust your matrix if your empirical test
   changes your assessment.

5. [ ] Write a brief `routing-policy.md`: one paragraph on how Meridian should route the five
   task categories, citing the three axes. Reference at least one OWASP LLM risk by ID.

## Success criteria — you're done when
- [ ] All five blank rows in `data/decision-matrix.md` are filled with a routing decision and
  rationale.
- [ ] You have run at least two prompts through the local model and documented the quality gap
  between local and frontier for those tasks.
- [ ] `routing-policy.md` exists and cites at least one OWASP LLM risk (e.g. LLM06 or LLM09).

## Deliverables
`data/decision-matrix.md` (your completed matrix) + `routing-policy.md` (the one-paragraph
policy). Commit both. These are the start of Meridian's AI governance documentation.

## Automate & own it
**Required.** Write a Python script `check_routing.py` that reads a task description from stdin
and prints the recommended routing (Local / Frontier / Human) based on a set of heuristics you
define (keyword patterns, sensitivity flags, etc.). Have a model draft the heuristic logic; you
review every condition and add at least two that the model missed. Run it against the five tasks
from your matrix and confirm the output matches your manual decisions. Commit the script.

## AI acceleration
Have a model help populate the decision matrix — give it the three axes as a system prompt and
each task category as a user message, asking it to recommend a routing and rationale. Then
review every cell: the model doesn't know Meridian's data classification policy. Correct anything
that conflicts with the sensitivity constraints you'd actually have in a real environment.

## Connects forward
The routing framework you build here is the policy layer that governs every subsequent module.
Module 02 (Running Local Models) explores *how* the local tier actually works; Module 09 (Securing
the AI You Run) revisits routing as an attack surface — a prompt injected into an alert can try
to change the routing decision at inference time.

## Marketable proof
> "I can design an AI task-routing policy for a security team — deciding what runs locally for
> data residency, what uses a frontier model, and what stays human-only — and I can justify each
> decision against OWASP LLM risks."

## Stretch
- Add a fourth column to the matrix: "Acceptable error rate." Define what "wrong" looks like
  for each task and whether the consequence is recoverable. This is the foundation of an AI
  governance risk assessment.
- Implement the routing check as an MCP tool (covered properly in Module 05) so an LLM can
  call it to route its own sub-tasks.
