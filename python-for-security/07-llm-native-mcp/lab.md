# Lab 07 — Make `sift` LLM-Native (MCP + Typed Output)

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/07-llm-native-mcp/`: the `sift` project, the MCP SDK and `instructor`
installed, and the MCP Inspector for driving your server like a client.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/07-llm-native-mcp
make up
make shell
make demo    # starts the sift MCP server and exercises the enrich tool + a typed LLM verdict
make down
```

Reproducible at zero cost. LLM calls use a key you supply via env (`pydantic-settings`, from Module 02)
or a local model; the MCP server runs offline.

## Scenario

`sift` has a safe, typed core (Modules 02–06). Now you'll make it LLM-native: expose its enrich/triage as
an MCP server an agent can call, and let `sift` itself call an LLM to classify an alert — validating the
model's output like any other untrusted upstream.

> Only test systems you own or have explicit written permission to test.

## Do

1. [ ] **Expose `sift` as an MCP server.** Wrap the enrich/triage functions as `@mcp.tool()`s; let the
   type hints and docstrings define the schema. Run it and drive it with the MCP Inspector.
2. [ ] **Treat the LLM as an untrusted caller.** Validate every tool argument with Module 02's `pydantic`
   models *inside* the tool. Prove it: pass a hostile argument (e.g. a non-indicator string / injection
   payload) and confirm the tool rejects it rather than acting on it.
3. [ ] **Keep tools read-only (or gate them).** Ensure the exposed tools don't mutate state; if one must,
   put a human-confirmation gate in front of it.
4. [ ] **Validate the LLM's output.** Have `sift` call a model to classify an alert, and use `instructor`
   to coerce the reply into a `Verdict` pydantic model — no `json.loads()` of free text. Show it re-asking
   or failing cleanly on a malformed response.
5. [ ] **Automate & own it.** Commit the MCP server and the `instructor`-typed classifier into `sift`.
   Note what the copilot generated and which boundary it skipped (unvalidated tool args, or untyped LLM
   output).

## Success criteria — you're done when
- [ ] `sift`'s enrich/triage are callable as MCP tools (verified with the Inspector or a client).
- [ ] Tool arguments are validated with `pydantic`; a hostile argument is rejected, not acted on.
- [ ] Exposed tools are read-only, or state-changers sit behind an explicit human gate.
- [ ] An LLM classification returns a **validated `pydantic` model** via `instructor`, not parsed text.

## Deliverables
The updated `sift` repo: the MCP server module, the `instructor`-typed classifier, and a note on the two
trust boundaries (tool args in, model output out) and how each is validated. Do **not** commit API keys —
load them via `pydantic-settings`/env.

## AI acceleration
The whole module is about the AI edge, so review there: the copilot will happily expose a tool that trusts
its arguments and a classifier that `json.loads()` the model's prose. Both are the same unvalidated-input
bug you've caught since Module 02 — now catch it where the untrusted upstream is the model itself.

## Connects forward
The MCP server you build here is the exact target Module 08 red-teams (prompt injection against your own
`enrich` tool). The typed-output discipline connects to Module 09's eval harness — you can only measure a
classifier whose output has a stable, typed shape. Track 12 takes this into operating AI systems at scale.

## Marketable proof
> "I make Python security tools LLM-native — exposing them as MCP servers that validate every
> model-supplied argument, and validating LLM output into typed `pydantic` models with `instructor`
> instead of trusting free text."

## Stretch (optional)
- Register the `sift` MCP server with a real MCP client (e.g. Claude Code) and call it end to end.
- Add a second tool that would be dangerous if unguarded (a state-changer) and implement the
  human-confirmation gate, proving the model can't trigger it unattended.
