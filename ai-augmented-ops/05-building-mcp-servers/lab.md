# Lab 05 — Build a tested MCP server

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 9 · Tool-Build (+ Type 7 Build-&-Operate).** You ship a reusable MCP server — typed,
schema-validated tools any MCP client can call — and a **test suite** that proves each tool is
correct on good input *and rejects a malformed or hostile argument instead of executing it*.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/05-building-mcp-servers
make up && make demo
```

**Requirements:** Docker, 2 GB RAM free. No GPU, no Ollama — this module is about the protocol and
the tool contract, not inference. `make demo` starts the server and calls each tool with a test
input (including one deliberately malformed argument), printing the JSON response so you can see the
validation path fire.

## Scenario
A security team wants to give its AI assistant access to *live* data — the real alert database and
incident records, not training data. Your job: build an MCP server that exposes that data as
reusable, schema-validated tools, and **prove the tools hold up** — they return correct results on
good input and refuse hostile input — *before* anyone wires them to a model in module 06. The tools
are the product; the tests are the proof they're safe to ship.

> Everything runs locally against bundled seed data. No external targets, no authorization needed.
> The tools you build here become an attack surface in module 09 — which is exactly why you test
> them now.

## Do

1. [ ] **Run it and read the contract.** `make demo` and, for each tool call, identify:
   - the **tool name and arguments** sent in the request,
   - the **JSON response** returned, and whether it's machine-parseable (`json.loads()`),
   - what the **malformed-argument** demo call returns — a structured error dict, or a crash?

2. [ ] **Read the tool source.** `make shell`, then open `server/server.py`. For each tool, answer:
   - How is the schema derived from the function signature + docstring? (What does the model *see*?)
   - What happens if `ioc` in `get_threat_intel` is an injection-style string
     (`'; DROP TABLE iocs; --`) — is it validated *before* use, or after?
   - Does `search_alerts` handle an empty result set, an empty query, and an over-long query
     without raising?

3. [ ] **Add a fourth tool** — `list_open_incidents()` — backed by `data/incidents.json`, returning
   open incidents' IDs, titles, and severity. Give it a precise, model-readable docstring (it *is*
   the schema). Run `make demo`; confirm it appears in the tool list and returns valid JSON.

4. [ ] **Harden the input contract (every argument is untrusted).** With a model drafting and you
   reviewing every line, make each tool reject bad input as a **structured error dict**, never an
   exception:
   - `get_threat_intel`: reject `ioc` longer than 255 chars or containing characters outside
     `[a-zA-Z0-9./:_@-]` (this is the tool-poisoning / injection guard).
   - `search_alerts`: reject empty/whitespace-only queries; cap results.
   - `list_open_incidents` (and `summarize_incident`): validate the ID format before lookup.
   Verify the edge cases yourself: Unicode, null bytes, excessively long strings, the empty string.

5. [ ] **Write the test suite — the deliverable.** Create `tests/test_tools.py` (pytest) with two
   classes of test per tool:
   - **Correctness:** a known-good argument returns the expected record/shape (e.g.
     `get_threat_intel("185.220.101.42")` is found and classified; `search_alerts("PowerShell")`
     returns ≥1 alert; the new tool lists the seeded open incidents).
   - **Validation / hostile-input:** a malformed or hostile argument is **rejected, not executed** —
     the SQL-injection-style `ioc` returns `{"error": ...}` (and the result must *not* contain a data
     record), the over-long string is refused, the empty query is refused, a bad incident ID is
     refused. Assert on *behaviour* (an error key present, no record returned), not just that the call
     didn't throw.
   Run `pytest` (or `make test`); all tests pass.

6. [ ] **Package it as a reusable tool.** Ensure `server/server.py` runs standalone, dependencies are
   pinned in `server/requirements.txt`, and a short `server/README.md` documents the tools, their
   schemas, the error contract, and how to run the server and the tests. A `make test` target runs
   the suite.

7. [ ] **Review the descriptions (AI-assisted).** Paste `server.py` into a frontier model and ask it
   to critique each tool description for clarity. Adopt what's genuinely sharper; note where its
   wording is imprecise for a security context. Leave a comment recording what you changed and why.

## Success criteria — you're done when *(honor system — self-verified; no grader)*
- [ ] `make demo` calls all original tools **and** the malformed-argument call returns a structured
  error dict (visible in the output), not a crash.
- [ ] Your fourth tool (`list_open_incidents`) is implemented, schema-documented, and appears in the demo.
- [ ] `tests/test_tools.py` exists and `pytest` (or `make test`) passes, with **at least one
  hostile-input test per tool** that asserts the bad argument is rejected and **no data record is returned**.
- [ ] Deliberately break a validation guard (e.g. remove the `ioc` regex check) and confirm the
  matching test **fails** — proof the test actually exercises the rejection path. Restore it.
- [ ] `server/README.md` documents each tool's schema, the error contract, and how to run the tests.

## Deliverables
The packaged MCP server (`server/server.py` with the fourth tool + validation, `server/requirements.txt`,
`server/README.md`) **and its test suite** (`tests/test_tools.py`). Commit all of them. Lab artifacts
(captures, scratch output) stay out of the commit.

## Automate & own it
**Required — and it's the test suite above.** The reusable artifact here is not just the server but
the *guarantee* that it's safe to call: turn "I checked the edge cases by hand" into
`tests/test_tools.py`, run on every change. Have the model draft the cases (especially the hostile
ones); you review every assertion and prove the suite bites by breaking a guard and watching a test
go red. A tool you can't re-prove on demand is a liability, not a component.

## AI acceleration
Two loops. **Drafting:** let the model write tool bodies and test cases — it knows the patterns.
**Adversarial review:** describe a hostile tool argument in natural language and ask the model to
generate the payload, then confirm your validation refuses it *and* your test captures it. Where the
model's suggested validation is too narrow (it allows a byte class you should block) or too broad (it
breaks a legitimate IOC), that gap is exactly the judgment you own.

## Connects forward
The MCP server you build here is the **data layer** for the SoC Copilot in module 06 — the model
calls these tools at inference time to answer live questions. And it is an **attack surface** in
module 09 (*Securing the AI You Run*): a hostile `ioc` or `query` argument is a prompt-injection
vector into the model's context, exactly the [tool-poisoning class Invariant Labs
disclosed](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks) and OWASP
catalogued as [MCP03:2025](https://owasp.org/www-project-mcp-top-10/2025/MCP03-2025%E2%80%93Tool-Poisoning).
Your validation tests become the regression suite that proves those attacks stay blocked after you
harden in module 09.

## Marketable proof
> "I build MCP servers in Python with fastmcp — exposing security data as typed, schema-validated
> tools any MCP-compatible client can call — with input validation, structured error contracts, and
> a pytest suite that proves each tool returns correct results and rejects hostile arguments instead
> of executing them."

## Stretch
- Implement a `require_confirmation` decorator for action-taking tools: a tool so marked prints a
  confirmation prompt and waits for explicit approval before executing. Apply it to a hypothetical
  `isolate_host(hostname)` stub — and add a test that it does *not* execute without approval.
- Add HTTP Bearer-token auth to the server (fastmcp supports it). Test that a call without the token
  returns 401.
