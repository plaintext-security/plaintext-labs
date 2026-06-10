# Lab 09 — Building an MCP Server

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/09-building-mcp-server
make up        # starts mock threat-intel API + MCP server container
make demo      # starts the server and makes a test tool call via the MCP client
make shell
make down
```

Two containers: the **mock threat-intel API** (reused from module 04) and the **MCP server
container** with `fastmcp`, `httpx`, and `python-dotenv` installed. `make demo` starts the
server and uses a small Python MCP client (`test_call.py`) to invoke the `enrich_ip` tool and
print the result — no LLM host required.

## Scenario
Meridian's security team wants to expose the IOC enrichment function to Claude so analysts can
ask "Is this IP malicious?" in a chat window and get an enriched answer immediately. Your task:
build an MCP server that exposes `enrich_ip` as a tool, backed by the mock API. The server must
validate input, handle API errors gracefully, and return a structured result the LLM can parse.

## Do
1. [ ] `make demo` — watch the test client call the reference `server.py` and print the enriched
   result for three IPs: one malicious, one clean, one that returns a 404 from the mock API.
2. [ ] Write `server.py` using `fastmcp`:
   ```python
   import fastmcp, httpx, os, re
   mcp = fastmcp.FastMCP("meridian-security")

   @mcp.tool
   def enrich_ip(ip: str) -> dict:
       """Enrich an IP address with threat-intel data from the Meridian API."""
       ...
   ```
   - Validate `ip` matches `r"^\d{1,3}(\.\d{1,3}){3}$"` before calling the API; return
     `{"error": "invalid IP format"}` on failure.
   - Query `http://threat-api:8080/api/v3/ip/<ip>` with a 10-second timeout.
   - Return the full parsed JSON response on 200; on 404 return `{"verdict": "unknown"}`;
     on other errors return `{"error": "api_error", "status": response.status_code}`.
3. [ ] Run the test client: `python test_call.py enrich_ip '{"ip": "8.8.8.8"}'`. Confirm it
   returns valid JSON.
4. [ ] Test the validation: call with `{"ip": "not-an-ip"}` — confirm it returns the error dict
   without raising an exception.
5. [ ] Test the 404 case: call with `{"ip": "1.2.3.4"}` (mock API returns 404 for this IP) —
   confirm `{"verdict": "unknown"}` is returned.

## Success criteria — you're done when
- [ ] `server.py` starts without error.
- [ ] The `enrich_ip` tool returns correct results for the malicious and clean IPs.
- [ ] Invalid IP format returns `{"error": "invalid IP format"}` (not a Python exception).
- [ ] Unknown IP (404) returns `{"verdict": "unknown"}`.
- [ ] `make demo` exits 0.

## Deliverables
`server.py` + `test_call.py` (the client used to verify). Commit both.

## Automate & own it
**Required.** Add a second tool: `enrich_hash(hash_value: str) -> dict` that validates the
input (must be 32 or 64 hex chars) and queries the mock VT hash endpoint. Have a model draft
the tool; review the input validation regex — does it reject a 63-character string? A 64-char
string with a non-hex character? Write two test calls in `test_call.py` that catch those edge
cases. Commit the extended server.

## AI acceleration
Ask a model to add docstrings to both tools — `fastmcp` uses the docstring as the tool
description in the schema. Read the generated description: is it accurate? Is it specific enough
that an LLM would call the right tool in context? The tool description is your prompt to the
LLM; own it.

## Connects forward
This MCP server is the integration target for any LLM-assisted investigation workflow. In the
Track 10 capstone, the SOAR playbook can call MCP tools rather than hard-coding API logic. The
server pattern also connects to Track 12 (AI-augmented ops) directly.

## Marketable proof
> "I've built a production-pattern MCP server that exposes security operations as typed tools
> an LLM can call — with input validation and structured error returns, not raw exception
> propagation."

## Stretch
- Add a `list_recent_iocs(limit: int = 10) -> list[dict]` tool that queries a mock "recent
  alerts" endpoint and returns the last N IOCs — giving an LLM a way to ask "what are we seeing
  right now?" without being prompted with specific IOCs.
- Connect the server to a real MCP client (Claude Desktop or Cursor) and verify the tool appears
  in the tool list and executes correctly.
