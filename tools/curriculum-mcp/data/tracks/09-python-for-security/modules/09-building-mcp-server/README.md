# Module 09 — Building an MCP Server

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *if you can describe a security operation as a function, you can hand it to an LLM.*

## Why this matters
The Model Context Protocol (MCP) is the emerging standard for giving LLMs access to tools and
data sources. A security team that exposes their threat-intel enrichment, SIEM search, and asset
lookup as MCP tools can let an AI assistant drive those operations while keeping a human in the
loop for decisions. This module is the practical entry point: build a real MCP server that wraps
the enrichment function you've already written.

## Objective
Build a `fastmcp` MCP server that exposes one tool — `enrich_ip(ip: str) -> dict` — backed by
the local mock threat-intel API from module 04. The server should start, respond to the MCP tool
protocol, and return enriched results in a format an LLM client can parse.

## The core idea
MCP is a JSON-RPC protocol over standard I/O or HTTP. A server declares a set of **tools** —
functions with typed input schemas and structured return values — and a client (Claude, Cursor,
or any MCP-aware host) can call those tools by name. The `fastmcp` library is to MCP what
`FastAPI` is to REST: you write a Python function with type hints, decorate it with `@mcp.tool`,
and `fastmcp` generates the schema and handles the protocol. From the LLM's perspective, the
tool looks like a typed function in the tool list it was given.

The security use case is concrete: an analyst prompts Claude with "Is this IP malicious?" and
Claude calls `enrich_ip("185.220.101.1")`, gets back `{"verdict": "malicious", "abuse_score":
95, "asn": "AS4444 TOR Exit"}`, and explains the result in plain English. The analyst never
leaves the chat window; the enrichment is automatic; the human provides the judgment ("yes,
block it"). This is the "AI authors → you review → you own it" posture applied to tool use:
the AI does the API call, you decide what to do with the result.

The operational discipline for MCP servers in security contexts: every tool should be read-only
unless the LLM is explicitly designed and scoped for write actions. An `enrich_ip` tool that
only queries is safe. An `block_ip(ip: str)` tool that writes a firewall rule is a tool that
can cause an outage if the LLM misunderstands a prompt. Build read-only first; add write tools
only with a human-approval step designed in from the start, not bolted on.

Input validation on every tool argument is not optional. An LLM will occasionally pass
malformed input — a partial IP, a domain where an IP was expected, or a value injected by a
prompt from an adversarial document (prompt injection). Validate the IP format before calling
the API; return a clear error message rather than letting the API call fail with a cryptic
status. The MCP server is a trust boundary: treat every tool argument as untrusted input.

## Learn (~2 hrs)

**MCP fundamentals (~1 hr)**
- [Model Context Protocol — Introduction (modelcontextprotocol.io)](https://modelcontextprotocol.io/docs/getting-started/intro) — read the "What is MCP?", "Core concepts", and "Tools" sections; understand the tool schema format and how clients discover tools.
- [fastmcp — GitHub README](https://github.com/PrefectHQ/fastmcp) — the library you'll use; read the "Quick start" and "Tools" sections; the decorator pattern is the entire API surface you need.

**Security considerations for MCP (~1 hr)**
- [MCP Security — Prompt Injection and Tool Safety (Simon Willison)](https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/) — Simon Willison's writing on MCP security is the clearest current thinking; read carefully, especially the prompt-injection risk for data-reading tools.
- [Anthropic — Tool use (function calling) guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview) — understand the tool schema format from the client's perspective so you know what your server must produce.

## Key concepts
- MCP tool schema: name, description, input schema (JSON Schema), return value
- `@mcp.tool` decorator: function signature → tool schema automatically
- Read-only vs write tools: the security boundary and why it matters
- Input validation as a trust boundary: every argument is untrusted
- Prompt injection risk: data your tool reads can contain instructions to the LLM

## AI acceleration
`fastmcp` is new enough that models sometimes get the decorator syntax slightly wrong. Write the
server function first, then ask a model to add the `@mcp.tool` decorator and the `fastmcp.FastMCP`
initialization. Test it by running the server and calling the tool directly — does it respond
with valid JSON that matches the schema? The model will get you 80% there; the remaining 20% is
usually the return type annotation and the error handling.
