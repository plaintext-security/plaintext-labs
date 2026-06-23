# Lab 01 — Route It, Then Defend It: An AI Task-Routing ADR

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

The lab ships one seed file: `data/decision-matrix.md` — the three routing axes, worked examples,
and the task rows you'll route. You feed the local model to gather *evidence*; the deliverable is the
**ADR** you defend on top of that evidence.

> Everything in this lab runs against local infrastructure you own. No external targets, no
> authorization concerns. This is a decision-and-design exercise with a live model as the test bench.

## Scenario

A financial-services security team has approved a pilot: use AI to pre-triage an alert queue before a
human analyst reviews it. Before any of it ships, *you* have to make and document the routing
decision — what runs on the local model, what (if anything) goes to a frontier API, and what stays
human-only — and defend it as an ADR a CISO could sign off on.

The stakes are not hypothetical. In **Moffatt v. Air Canada (2024 BCCRT 149)**, a tribunal held an
airline liable for a confident, wrong answer its chatbot gave a customer. The deploying organization
owned the output — full stop. Your routing table is the control that decides *where a confidently
wrong AI answer can do damage* in this SOC. That's what the ADR has to defend.

## Do

1. [ ] `make demo` and read the output. The demo asks `tinyllama` a single security question and
   reports latency and token throughput. Judge the answer: is it accurate? Is it the kind of
   confident-but-unverifiable output you'd be uncomfortable acting on without review? Note it — this
   is your first data point on "confidence ≠ accuracy."

2. [ ] **Gather routing evidence.** Open `data/decision-matrix.md`, read the three axes (sensitivity,
   reasoning complexity, recoverability) and the worked examples, then route the five blank task rows
   (Local / Frontier / Human + a one-line rationale each). This matrix is your evidence base, not the
   final deliverable.

3. [ ] **Probe the local model on a sensitive-data task.** `make shell`, then hit the API directly:
   ```bash
   curl -s http://localhost:11434/api/generate \
     -d '{"model":"tinyllama","prompt":"Summarize CVE-2021-44228 in one sentence.","stream":false}' \
     | python3 -m json.tool
   ```
   Compare the output to the NVD entry. Where is it right, where does it drift, and — critically —
   *does it signal any uncertainty when it's wrong?* (It won't. That's the point.)

4. [ ] **Stress-test the matrix.** Run the two tasks you marked "Local" through the model. Do the
   answers clear the bar you'd accept from a first-tier analyst? If the empirical result changes your
   call, change the matrix — and remember *why*, because the "why" goes in the ADR's Consequences.

5. [ ] **Write the ADR** (`routing-adr.md`) in Nygard format. This is the deliverable:
   - **Status:** Proposed.
   - **Context:** the forces — the data-residency / compliance constraint, the incident-time latency
     and vendor-dependency concern, and the *Moffatt* lesson (the org owns every AI output). 2–4
     sentences.
   - **Options:** the real choices for *this* pilot — e.g. (a) frontier-API-for-everything,
     (b) local-only, (c) **stakes-based hybrid** (local for sensitive/recoverable, frontier for
     scrubbed/high-complexity, human for irreversible). Give each option honest pros and cons.
   - **Decision:** the routing you recommend, in one sentence, and the one load-bearing reason.
   - **Consequences:** what you *accept* by choosing it — the honest downsides — plus a concrete
     **attack-path / liability note**: name one task where a confidently-wrong AI answer, if it
     slipped through your routing, would be irrecoverable, and state how your routing prevents it from
     being auto-acted-on. Cite at least one OWASP LLM risk by ID (LLM06 / LLM09).

## Success criteria — you're done when

- [ ] All five blank rows in `data/decision-matrix.md` are routed with a rationale.
- [ ] You ran at least two prompts through the local model and documented the gap between its
  confident output and ground truth for those tasks.
- [ ] `routing-adr.md` exists with all four Nygard sections — Context, **Options (≥2, each with
  honest cons)**, Decision, **Consequences (with the attack-path/liability note and ≥1 OWASP LLM
  ID)**. The negatives are as specific as the positives.

*Honor-system self-check:* re-read your Consequences section. If every line is upside, it's not done
— a defensible ADR names what you gave up and where you're still exposed.

## Deliverables

`data/decision-matrix.md` (your routing evidence) + **`routing-adr.md`** (the defended decision —
the portfolio artifact). Commit both. The ADR is the start of this team's AI governance record.

## Automate & own it

**Required.** Write `check_routing.py`: reads a task description on stdin and prints the recommended
routing (Local / Frontier / Human) from heuristics you define (keyword/sensitivity flags, an
irreversibility flag, a complexity flag). Have a model draft the heuristic logic; **review every
condition and add at least two the model missed** — at minimum a *recoverability* check (does acting
on a wrong answer cause irreversible harm? → escalate toward Human) so the script encodes the
*Moffatt* lesson, not just keyword matching. Run it against the five tasks from your matrix and
confirm it agrees with your manual calls; where it disagrees, decide which is right and fix the one
that's wrong. Commit the script.

## AI acceleration

Use a model to draft the ADR scaffold and the options table from your matrix notes — it's good at
that. Then **audit the Consequences**: ask it explicitly, "What are the negative consequences and new
risks of this routing?" and verify each against your real constraints. A model that lists only
benefits is doing the confident-but-unaccountable thing the whole module is about. You own the ADR;
the model only drafts it.

## Connects forward

The routing ADR you write here is the policy layer governing every later module. **02 (Running Local
Models)** explores *how* the local tier actually performs; **09 (Securing the AI You Run)** revisits
routing as an *attack surface* — a prompt injected into an alert can try to flip the routing decision
at inference time, turning a "human-only" task into an auto-acted one. The honest Consequences you
write now are the threat model 09 attacks.

## Marketable proof

> "I can design and defend an AI task-routing policy for a SOC as an ADR — deciding what runs locally
> for data residency, what uses a frontier model, and what stays human-only — grounded in a real
> liability ruling (Moffatt v. Air Canada) and justified against OWASP LLM risks with honest
> consequences."

## Stretch

- Add a fifth axis to the matrix and the ADR: **acceptable error rate**. Define what "wrong" looks
  like per task and whether the consequence is recoverable — the seed of an AI governance risk
  assessment, and the bridge to the eval harness in module 11.
- Re-implement `check_routing.py`'s logic as an MCP tool (covered in module 05) so an LLM can call it
  to route its own sub-tasks — and note in your ADR's Consequences why letting the model route itself
  is exactly the trust boundary module 09 will attack.
