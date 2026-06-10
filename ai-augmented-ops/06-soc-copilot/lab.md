# Lab 06 — A SoC Copilot (MCP + RAG)

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/06-soc-copilot
make up && make demo
```

**Requirements:** Docker, 8 GB RAM free. Three containers start: Ollama, ChromaDB, and the
copilot application. First run downloads `tinyllama` (~637 MB) and `nomic-embed-text` (~274 MB)
and ingests the knowledge base. `make demo` asks the copilot "Is 185.220.101.42 malicious?"
and prints the full reasoning chain: retrieved chunks, tool calls, and generated answer.

This lab depends on the data from Module 04 (knowledge base) and Module 05 (alert and incident
seed data). Both are bundled here — no need to complete those modules first.

## Scenario
Meridian's SOC team is testing their new copilot before going live. The copilot needs to answer
questions by combining institutional knowledge (past incidents, runbooks) with live data (current
alerts, threat intel lookups). Your job: validate the copilot against five realistic analyst
questions, document where it succeeds and where it fails, and implement one improvement.

> Test prompt injection and adversarial techniques only against models and applications
> you own or are authorised to assess.

## Do

1. [ ] `make demo` — the demo asks "Is 185.220.101.42 malicious?" Read the full output:
   - What chunks did RAG retrieve?
   - What tool was called (threat intel lookup)?
   - Did the generated answer accurately reflect the tool result and the retrieved context?
   - Is there any content in the answer not supported by the evidence shown?

2. [ ] Run four more questions through the copilot:
   ```bash
   make ask Q="What containment steps should I follow for a ransomware event?"
   make ask Q="Is there an open incident for host MERIDIAN-WKS-023?"
   make ask Q="What is the SLA for patching a Critical CVSS score vulnerability?"
   make ask Q="Summarise the credential phishing incident from 2024."
   ```
   For each, record in `results/copilot-evaluation.md`: were the retrieved chunks relevant?
   Did the answer cite the right source? Any hallucination-on-context?

3. [ ] Examine the copilot's reasoning transparency. Does the output clearly show which facts
   came from RAG, which from MCP tool calls, and which from the model's training? If not,
   what would you change in the prompt to make the provenance explicit?

4. [ ] Find one answer where the copilot was wrong or incomplete. Trace the failure:
   was it a retrieval miss (right document not returned), a tool call error (wrong tool
   called or bad argument), or hallucination-on-context (model fabricated detail)? Document
   your diagnosis in `results/copilot-evaluation.md`.

5. [ ] Implement one improvement to `copilot/copilot.py` — either fix the retrieval
   miss you found, improve a tool-call heuristic, or strengthen the system prompt's
   provenance instructions. Re-run the failing question and confirm improvement.

## Success criteria — you're done when
- [ ] `make demo` completes and prints the full reasoning chain.
- [ ] `results/copilot-evaluation.md` has notes for all five questions.
- [ ] One failure mode is diagnosed with root cause.
- [ ] One improvement is implemented and validated.

## Deliverables
`copilot/copilot.py` (with your improvement) + `results/copilot-evaluation.md`. Commit both.
The copilot is the attack target for Module 09.

## Automate & own it
**Required.** Write `scripts/batch-query.py` — reads a list of questions from
`data/eval-questions.txt` (one per line), runs each through the copilot, and writes a
Markdown table of question / retrieved-sources / answer-preview / hallucination-observed
to `results/batch-eval.md`. Have a model draft the table-formatting and async-request
logic; you add the hallucination-check heuristic (e.g. flag any answer containing a
specific CVE ID that isn't in the knowledge base). Commit the script and the batch results.

## AI acceleration
Paste the copilot's generated answer alongside the retrieved chunks into a frontier model
and ask it to identify any claims in the answer not supported by the context. This "hallucination
auditor" pattern is the fast path to finding hallucination-on-context before it reaches an analyst.

## Connects forward
This copilot is the attack target for Module 09 (Securing the AI You Run) — prompt injection
via alert text, context poisoning via a malicious knowledge-base document, and tool result
manipulation are all demonstrated against this stack. Build it well so you can understand
what you're attacking.

## Marketable proof
> "I built a SoC copilot that combines RAG over a private knowledge base with live MCP tool
> calls — answering analyst questions with full evidence traceability and a documented
> failure-mode analysis."

## Stretch
- Add a confidence score to the copilot's output: after generating the answer, send a follow-up
  prompt asking the model to rate its confidence on a 1–5 scale and flag which claims it is
  least certain about. Display this alongside the answer.
- Implement a "source must be cited" constraint: modify the system prompt to require the model
  to end every factual claim with `[source: <filename>]`. Validate programmatically that every
  citation references a file that actually exists in the knowledge base.
