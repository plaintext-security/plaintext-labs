# Lab 07 — LLM-Native PowerShell & an MCP Surface

Environment for **Track 13 · Module 07**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/07-llm-native-mcp/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer + Pester container
make shell   # drop into pwsh with the Vigil module + MCP handler
make demo    # run the gate (PSScriptAnalyzer + Pester) over the MCP surface, offline
make down    # stop when done
```

- `Vigil/` — the cumulative module. `Public/` carries the read-only hunt verbs (`Get-VigilEvent`,
  `Read-VigilEnrichment`) plus the **MCP surface** (`Get-VigilMcpToolDefinition`, `Invoke-VigilMcpRequest`).
  `Private/` carries the security core: the **read-only tool registry** (an explicit allow-list) and the
  **validation layer** that treats every model-supplied tool argument as untrusted input.
- `Vigil.Tests.ps1` — proves a well-formed `tools/call` returns objects, each hostile/malformed argument is
  rejected by validation, and no state-changing verb is exposed.
- `data/sample.json` — a small Windows-event export (7 events; 3 suspicious).
- `data/threatfeed.json` — a bundled threat-feed snapshot for the enrichment lookup.

The demo is **fully offline and deterministic**: it drives the MCP handler with good and hostile JSON-RPC
payloads directly — no live LLM, no network. Wiring the same handler to a real MCP client (Claude Desktop, or
the Claude API's MCP connector) is a config step outside this repo; the validation layer is transport-agnostic.
