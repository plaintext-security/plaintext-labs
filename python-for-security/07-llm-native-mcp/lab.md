# Lab 07 — Make `sift` LLM-Native (MCP + Typed Output)

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/07-llm-native-mcp` (a container with
> the `sift` project, the Python MCP SDK + `instructor`, the MCP Inspector, and a bundled **real Suricata
> `eve.json`** — a STRRAT RAT infection). Objective: **expose `sift`'s existing enrich/triage over an MCP
> server and validate the LLM on both sides** — every tool argument the model passes in, and every reply
> the model gives back. Target: **~2–3 hrs.**
> *Intermediate-plus: the steps state objectives; you derive the MCP/`instructor` code (with the copilot).*

> **This lab exposes the *same* `sift`.** You are not building a new tool — you are adding one surface (an
> MCP server) to the `sift` you grew in Modules 02–06, so an agent can call its enrich/triage and so `sift`
> can safely call an LLM. The typed core (`AlertEvent`, `IPvAnyAddress`) does the validating; MCP and
> `instructor` are just the new I/O.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **An MCP server is an API whose caller is an LLM.** | The model is an *untrusted caller* — it can be prompt-injected into calling your tool with a hostile argument. |
| 2 | **Same discipline as Module 02: parse at the boundary.** | An LLM-supplied tool argument is just another untrusted `eve.json` line — validate it into a typed model *inside* the tool. |
| 3 | **`instructor` makes LLM output a typed object, not a hope.** | Validate the reply like an API response into a `Verdict`; never `json.loads()` the model's free text and pray. |
| 4 | **Read-only by default; gate state-changers behind a human.** | The model must not be able to trigger a side effect unattended. |
| 5 | **Two boundaries = two OWASP LLM risks.** | *Prompt Injection* (arg in) and *Insecure Output Handling* (reply out) — the AI edge of the parse-don't-trust through-line. |
| 6 | **One `sift`, three edges of one discipline.** | Input (M02) · LLM output (M07) · measurement (M09) — same validation, three places. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea), and the OWASP Top 10 for LLM Applications (*Prompt Injection*,
> *Insecure Output Handling*).

---

## Warm-up — answer before you build (2 min)

1. Why is an argument the LLM passes to your MCP `enrich` tool "untrusted input," and what exactly stops
   `"1.1.1.1; DROP TABLE alerts"` from being dangerous?
2. How is validating an `instructor` reply into a `Verdict` the *same* discipline as validating a Suricata
   feed into an `AlertEvent`?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/07-llm-native-mcp
make up      # build the container: sift + MCP SDK + instructor + Inspector
make shell   # drop into the project (sift_reference/ + the real STRRAT eve.json)
make demo    # proves both boundaries offline: MCP arg validation + typed LLM output
make down
```

`make demo` runs the reference proof **without calling a real model**: it registers `sift`'s `enrich`/`triage`
as MCP tools, rejects a hostile IP arg and an out-of-range `alert` record at the tool boundary, and accepts a
well-formed model reply while rejecting a malformed one. LLM calls in your own build use a key you supply via
env (`pydantic-settings`, from Module 02) or a local model; the MCP server itself runs offline.

> **Authorization note.** Everything runs locally in the lab container against bundled sample data — only
> test systems you own or have explicit written permission to test.

---

## Build it — objective, then a signal (intermediate-plus: you drive the code)

### Step 1 — Expose `sift` as an MCP server

**Concept (30 sec):** Flight-card #1. Wrap `sift`'s existing enrich/triage as `@mcp.tool()`s over the **real
EVE-derived indicators** it already produces — a `src_ip`/`dest_ip` or a `signature` off a validated
`AlertEvent`, not an invented indicator blob. The type hints and docstrings *become* the schema the model sees.

**Do:** register the two tools on a `FastMCP` server and drive them with the MCP Inspector (or a client).

> **▸ On track if:** an LLM host / the Inspector **lists and calls** `sift`'s `enrich` and `triage` tools
> over MCP, and each tool's schema came from your type hints + docstring — not a hand-written JSON schema.

### Step 2 — Treat the LLM as an untrusted caller

**Concept (30 sec):** Flight-card #2. Every argument the model passes is untrusted input. Validate it with
the canonical EVE `pydantic` models *inside* the tool — an `IPvAnyAddress` for an IP indicator, `AlertEvent`
for a whole record — before the tool does anything.

**Do:** add the validation, then attack it: pass a hostile IP arg (`"1.1.1.1; DROP TABLE alerts"`, a non-IP
string) and a poisoned record (an `alert.severity` of `5`, outside Suricata's `1..3`).

> **▸ On track if:** the hostile IP arg **and** the out-of-range record are both **rejected at the tool
> boundary** (a `ValueError` / `ValidationError`), not acted on — exactly as Module 02 rejects a bad feed line.

### Step 3 — Keep the tools read-only (or gate them)

**Concept (30 sec):** Flight-card #4. A model that can call a tool can be *made* to call it. Prefer read-only.

**Do:** confirm the exposed tools don't mutate state; if you add one that must, put an explicit
human-confirmation gate in front of it.

> **▸ On track if:** no exposed tool changes state on its own — and any state-changer **cannot** be triggered
> by the model without a human in the loop.

### Step 4 — Validate the LLM's output with `instructor`

**Concept (30 sec):** Flight-card #3. When `sift` asks a model to classify an alert, you want a validated
`Verdict(severity, is_true_positive, rationale)` — not a paragraph you regex. `instructor` coerces the reply
into the `pydantic` model and re-asks on failure. This is the *exact twin* of Module 02: an untrusted upstream
validated into a typed object.

**Do:** have `sift` call a model (or use the offline `parse_model_reply` shim) to produce a `Verdict`; then
feed it a malformed reply (bad enum, missing field) and watch it reject rather than pass through.

> **▸ On track if:** a well-formed reply parses to a typed `Verdict`, and a malformed structured-output is
> **rejected** (or re-asked) rather than passed downstream — no `json.loads()` of free text anywhere.

---

## Prove the control (your finish line)

Commit the LLM-native `sift` and confirm the whole surface holds — **typed, validated I/O in both directions**:

- [ ] `sift`'s enrich/triage are callable as MCP tools (verified with the Inspector or a client).
- [ ] Tool arguments are validated with `pydantic`; a hostile IP arg **and** an out-of-range record are
      rejected, not acted on.
- [ ] Exposed tools are read-only, or a state-changer sits behind an explicit human gate.
- [ ] An LLM classification returns a **validated `Verdict`** via `instructor`; a malformed reply is rejected.

---

## Recall check — close the doc, answer from memory (3 min)

1. In one sentence: why is an MCP server "an API whose caller is untrusted," and what validates each argument?
2. What breaks the moment you `json.loads()` an LLM's reply instead of validating it into a `Verdict`?
3. Name the three edges of the parse-don't-trust through-line and the module each lives in.

---

## Deliverables

The updated `sift` repo: the MCP server module (enrich/triage as validated `@mcp.tool()`s), the
`instructor`-typed classifier, and a note on the **two trust boundaries** (tool args in, model output out)
and how each is validated. Do **not** commit API keys — load them via `pydantic-settings`/env. Lab artifacts
(captures, raw model dumps) stay out of commits.

## Automate & own it

**Required.** Commit the MCP server and the `instructor`-typed classifier into `sift`. Have the copilot
scaffold both — then review the two boundaries and note, in the commit/PR, **which one it skipped**: the copilot
will happily expose a tool that trusts its arguments and a classifier that `json.loads()` the model's prose.
Both are the same unvalidated-input bug you've caught since Module 02 — now at the AI edge. Record what it
generated, what you corrected, and the boundary it defaulted to leaving open.

## Definition of done (`llm-native-mcp` ✅)

- [ ] `sift` exposes enrich/triage over MCP; a host lists and calls them.
- [ ] Both boundaries are enforced: every tool argument is validated in, and every model reply is validated out.
- [ ] Tools are read-only (or gated); no unattended side effect the model can trigger.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

The MCP server you build here is the exact target **Module 08** red-teams (prompt injection against your own
`enrich` tool). The typed-output discipline connects to **Module 09's** eval harness — you can only measure a
classifier whose output has a stable, typed shape. **Track 12** takes this into operating AI systems at scale.

## Marketable proof

> "I make Python security tools LLM-native — exposing them as MCP servers that validate every model-supplied
> argument, and validating LLM output into typed `pydantic` models with `instructor` instead of trusting free
> text."

## Stretch (optional)

- Register the `sift` MCP server with a real MCP client (e.g. Claude Code) and call it end to end.
- Add a second tool that would be dangerous if unguarded (a state-changer) and implement the
  human-confirmation gate, proving the model can't trigger it unattended.
- **Dissector rung — a `dissect_eve_line` MCP tool.** Expose a tool that takes one **arbitrary raw
  `eve.json` line** (a string the model supplies — maximally untrusted) and returns either the typed event or
  a quarantine result. Route it through `sift`'s growing discriminated union (`alert` plus the dissector
  members added in M02 `dns`, M03 `http`, M04 `tls`, M05 `flow`/`fileinfo`): validate with
  `TypeAdapter(EveEvent)` *inside* the tool, and on any failure — non-JSON, an out-of-range `alert.severity`,
  or an `event_type` with no union member — return a structured quarantine object rather than raising to the
  model. This is untrusted-tool-argument validation at its purest: the model hands you a whole line, and the
  same union that guards `sift`'s ingest now guards its MCP surface.
  *Acceptance:* a well-formed line of a supported `event_type` returns the correct typed member; a malformed
  or unhandled-`event_type` line returns a quarantine result (never an unhandled exception across the tool
  boundary).
