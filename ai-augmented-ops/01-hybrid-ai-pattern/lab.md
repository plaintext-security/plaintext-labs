# Lab 01 — Route It, Then Defend It: an AI task-routing ADR

> **Hands-on lab.** Environment: `plaintext-labs/ai-augmented-ops/01-hybrid-ai-pattern`.
> Objective: **route a set of security tasks across local / frontier / human and defend the routing as
> an ADR a CISO could sign** — with a live local model as your test bench. Target: **~90 min**, one
> finish line. Runs entirely on **local infrastructure you own** (Ollama + `tinyllama`, CPU-only).

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Confidence ≠ accuracy.** | A fluent, specific answer can be flat wrong — and gives no uncertainty signal (Moffatt). |
| 2 | **You own the output.** | Deployment, not authorship, decides liability. No "the AI said it" defence. |
| 3 | **Route on three axes:** sensitivity · reasoning complexity · **recoverability**. | Recoverability is the load-bearing line — it decides what can be auto-acted. |
| 4 | **Local / frontier / human.** | Local = private/fast/lower ceiling; frontier = deeper/billed/leaves the boundary; human = the irreversible call. |
| 5 | **Data residency is a compliance posture,** not a latency preference. | The routing table that ignores it is the one Moffatt (and EchoLeak/LLM06) punishes. |
| 6 | **The ADR is the deliverable** — options scored, decision defended, **honest** consequences. | There's no "right" routing table; there's the one you can defend. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [reveal](README.md#the-reveal-confidence-is-not-accuracy-and-you-own-the-output) and the routing table.

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A local 7B model gives a **confident, specific** answer about a CVE. Name the one thing its
   confidence tells you about its **accuracy** — and the case that proves it.
2. Of the three routing axes, which one decides whether a task's output may be **auto-acted on**
   without a human — and why?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/01-hybrid-ai-pattern
make up && make demo
```

**Requirements:** Docker, ~4 GB RAM free, no GPU. First `make up` pulls the Ollama image (~1 GB) and
`tinyllama` (~637 MB); later runs use the cache. Seed file: **`data/decision-matrix.md`** — the three
axes, worked examples, the two real anchors (Moffatt; EchoLeak CVE-2025-32711), and the blank task
rows you route.

> **▸ On track if:** `curl -s http://localhost:11434/api/tags` lists `tinyllama` (the model pulled and
> Ollama is reachable on the published host port).

> **Authorization note.** Everything here runs against local infrastructure you own — no external
> targets. This is a decision-and-design exercise with a live model as the test bench. (Later modules
> *attack* AI systems; there the rule binds: only test systems you own or have written permission to test.)

---

## Build it — read a little, do a little

### Step 1 — Watch "confidence ≠ accuracy" happen (your first data point)

**Concept (30 sec):** Flight-card #1. A local model answers fast and sounds sure. Sureness is not a
truth signal — that's the whole Moffatt lesson, live on your machine.

**Do it:** `make demo` — it asks `tinyllama` one security question and prints the answer plus latency
and token throughput. Read the answer critically: would you *act* on it unreviewed?

> **▸ On track if:** the output shows an `ANSWER:` block and a `Latency: … | Tokens … | Throughput …
> tok/s` line. Note whether the answer flags any uncertainty when it's shaky (it won't — that's the point).

### Step 2 — Probe a sensitive-data task and compare to ground truth

**Concept (30 sec):** Flight-card #5. Some tasks carry internal/sensitive data; those favour the
**local** tier so the data never crosses the boundary (the EchoLeak / LLM06 exposure).

**Do it (from the host — the port is published):**
```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"tinyllama","prompt":"Summarize CVE-2021-44228 in one sentence.","stream":false}' \
  | python3 -m json.tool
```
Compare the `response` to the real NVD entry (Log4Shell). Where is it right, where does it drift, and
does it *signal* when it's wrong?

> **▸ On track if:** you get JSON with a non-empty `"response"` field, and you can name at least one
> place it drifts from ground truth **without** the model hedging.

### Step 3 — Route the matrix (your evidence base)

**Concept (30 sec):** Flight-card #3. Score each task on sensitivity · complexity · recoverability;
the route falls out. Recoverability is the line that sends a task to **human**.

**Do it:** open `data/decision-matrix.md`, read the axes + worked examples + the two anchors, then
route the blank task rows (**Local / Frontier / Human** + a one-line rationale each).

> **▸ On track if:** every blank row has a route **and** a rationale, and at least one row is Human-only
> *because it's irreversible* (not merely sensitive).

### Step 4 — Stress-test your "Local" calls against the model

**Do it:** run the two tasks you marked **Local** through the model (Step-2 pattern). Do the answers
clear the bar you'd accept from a first-tier analyst? If the empirical result changes a call, change
the matrix — and remember *why* (it goes in the ADR's Consequences).

> **▸ On track if:** at least one routing call is now backed by an observed model result, not just a
> guess — and you can state the "why" for any change.

---

## Prove the control (your finish line)

Write **`routing-adr.md`** in Nygard format — the deliverable, re-checked against the honesty bar:

- **Context** — the forces: data-residency/compliance, incident-time latency + vendor dependency, and
  the Moffatt lesson (the org owns every AI output). 2–4 sentences.
- **Options** — ≥2 real choices (frontier-for-everything · local-only · **stakes-based hybrid**), each
  with honest pros **and cons**.
- **Decision** — the routing you recommend, in one sentence, with the one load-bearing reason.
- **Consequences** — what you **accept**: the honest downsides, plus a concrete **attack-path /
  liability note** (name one task where a confidently-wrong answer would be irrecoverable, and how your
  routing stops it being auto-acted-on). Cite ≥1 OWASP LLM risk by ID (**LLM06** / **LLM09**).

**The honesty check (the real finish line):** re-read Consequences. **If every line is upside, it's not
done** — a defensible ADR names what you gave up and where you're still exposed.

---

## Recall check — close the doc, answer from memory (3 min)

1. The two Moffatt findings — state both, and why the second kills the "the AI said it, not us" defence.
2. The three routing axes — and which one decides auto-action.
3. Which task type stays **human-only** no matter how good the model gets, and what the model may still do for it.

---

## Deliverables

- **`routing-adr.md`** — the defended routing decision (portfolio artifact; the start of this team's AI
  governance record).
- `data/decision-matrix.md` — your routing evidence, filled in.

Commit both. *(Do not commit real internal data; the matrix is the fictional pilot.)*

## Automate & own it

**Required.** Write `check_routing.py`: reads a task description on stdin and prints the recommended
route (Local / Frontier / Human) from heuristics you define (sensitivity flags, an **irreversibility**
flag, a complexity flag). Have a model draft the logic — then **review every condition and add ≥2 it
missed**, at minimum a *recoverability* check (acting on a wrong answer causes irreversible harm →
escalate toward Human) so the script encodes the *Moffatt* lesson, not just keyword matching. Run it
against your five tasks; where it disagrees with your manual call, decide which is right and fix the
wrong one. Commit the script.

## Definition of done (`hybrid-ai` ✅)

- [ ] All blank rows in `data/decision-matrix.md` are routed with a rationale; ≥1 Human-only *for irreversibility*.
- [ ] ≥2 prompts run through the local model, with the confident-vs-correct gap documented.
- [ ] `routing-adr.md` has all four Nygard sections; Consequences names honest downsides + an attack-path/liability note + ≥1 OWASP LLM ID.
- [ ] `check_routing.py` agrees with your manual routing (or the disagreement is resolved).
- [ ] You can explain all six flight-card facts cold.

## Connects forward

The routing ADR is the policy layer for the whole track. **02 (Running Local Models)** explores how the
local tier actually performs; **09 (Securing the AI You Run)** revisits routing as an *attack surface* —
a prompt injected into an alert can try to flip a "human-only" task into an auto-acted one. The honest
Consequences you write now are the threat model 09 attacks.

## Marketable proof

> "I can design and defend an AI task-routing policy for a SOC as an ADR — deciding what runs locally
> for data residency, what uses a frontier model, and what stays human-only — grounded in a real
> liability ruling (Moffatt v. Air Canada) and justified against OWASP LLM risks with honest consequences."

## Stretch

- Add a fifth axis — **acceptable error rate**: define what "wrong" looks like per task and whether the
  consequence is recoverable (the seed of an AI governance risk assessment, and the bridge to the eval
  harness in module 11).
- Re-implement `check_routing.py` as an MCP tool (module 05) so an LLM can call it to route its own
  sub-tasks — and note in Consequences why letting the model route itself is exactly the trust boundary
  module 09 attacks.
