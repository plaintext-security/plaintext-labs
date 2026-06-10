# Module 05 — Building MCP Servers

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *MCP is the USB port for AI tools: write the tool once, and any compliant client can call it.*

## Why this matters
A language model alone can reason, but it cannot act — it cannot query a live threat feed, search
an alert database, or look up an incident ticket. The Model Context Protocol (MCP) is the open
standard that fixes this: it defines a clean JSON-RPC interface by which an AI agent (the MCP
client) calls tools exposed by an MCP server. Write a tool as a Python function, expose it via
fastmcp, and any MCP-compatible AI (Claude, a local Ollama agent, an n8n AI node) can discover
and call it at inference time. This is how you turn a reasoning model into a reasoning agent.

## Objective
Build and run an MCP server with three security-relevant tools, call each tool via the MCP
protocol, and understand what the tool-call flow looks like from both the server and client side.

## The core idea
MCP is a thin protocol layer, not a framework. At its core: the client sends a
`tools/call` JSON-RPC request with the tool name and arguments; the server executes the
function and returns a structured result; the client injects the result into the model's
context for the next generation step. The model never executes code directly — it generates
a request, the server runs it, and the model receives the output as text. This clean
separation is important for security: the model decides *what* to call, the server decides
*whether* to run it. Access control, rate limiting, and input sanitisation all live in the
server, not in the model.

`fastmcp` is a Python library that reduces MCP server boilerplate to almost nothing: decorate
a function with `@mcp.tool()`, and fastmcp handles the JSON-RPC plumbing, the tool schema
generation (from your function signature and docstring), and the transport layer. The tool
schema is generated automatically from Python type annotations — `ioc: str` becomes a
required string parameter in the tool manifest, which the model sees and uses to construct
its tool call. This tight coupling between code and schema is one of fastmcp's strongest
properties: the schema can't drift from the implementation because they're the same source.

For a security team building tools, the MCP pattern has an important operational consequence:
every tool is a trust boundary. A tool that calls `get_threat_intel(ioc)` is performing a
lookup on external infrastructure; a tool that calls `isolate_host(hostname)` is taking an
irreversible action. The same model that calls both has no inherent understanding of that
difference. The server must enforce the distinction: read-only tools can be called freely,
action-taking tools need confirmation, and certain actions (blocking a network path, deleting
data) should require an out-of-band approval step. The architecture decision of "what gets a
tool" is a security architecture decision.

The discovery mechanism is also worth understanding: when an MCP client connects, it calls
`tools/list` to get the server's full tool manifest. The model sees the tool names,
descriptions, and parameter schemas — that's all. A well-written tool description is a form
of documentation that the model reads at inference time. A vague description
(`search(query: str)`) produces vague tool calls; a precise one
(`search_alerts(query: str) — search the Meridian alert database for alerts matching the given keyword or IOC`)
produces precise ones. Write tool descriptions like API documentation for an engineer
who's never seen your codebase — because the model hasn't.

## Learn (~2.5 hrs)

**The MCP specification (~1 hr)**
- [Model Context Protocol — Introduction](https://modelcontextprotocol.io/docs/getting-started/intro) — the official spec site; read "Core concepts" and "Tools" sections. The protocol is simple; understanding the lifecycle (init → list tools → call tool → result) takes 20 minutes.
- [fastmcp documentation](https://gofastmcp.com/getting-started/welcome) — the library you'll use; read the "Quickstart" and "Tools" sections. Note how the schema is derived from type annotations.

**Agent architecture (~1 hr)**
- [Anthropic, "Building effective agents" (blog post)](https://www.anthropic.com/engineering/building-effective-agents) — the clearest framing of when to use tools vs. when to use RAG vs. when to use neither; the "augmented LLM" pattern is exactly what this module implements.
- [Simon Willison, "The MCP problem" (blog post)](https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/) — why MCP servers are prompt-injection targets; essential reading before Module 09, but understand the risk now.

**Security tool design (~30 min)**
- [OWASP Top 10 for LLM — LLM07 (Insecure Plugin Design)](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — the top risk in building MCP-style tools; the checklist applies directly to the tools you build in this module.

## Key concepts
- MCP as a JSON-RPC protocol: tools/list → tools/call → result
- fastmcp: schema from type annotations, tool description as model-readable API doc
- Tool trust hierarchy: read-only vs. action-taking vs. requires-confirmation
- Tool description quality directly drives model tool-call quality
- Every tool is a trust boundary: access control and input sanitisation live in the server

## AI acceleration
Have a model help write the tool function bodies — it knows both Python and JSON-RPC patterns
well. Your job is to review the input validation (does the tool sanitise the `ioc` string before
using it in a query?), the error handling (what does the tool return if the data file doesn't
exist?), and the tool description (is it precise enough for a model to use correctly?). The model
writes the function; you own the security boundary.
