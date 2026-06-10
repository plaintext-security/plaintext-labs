# Lab 05 — Building MCP Servers

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/05-building-mcp-servers
make up && make demo
```

**Requirements:** Docker, 2 GB RAM free. No GPU, no Ollama — this module is about the
protocol, not inference. `make demo` starts the MCP server and calls each of the three
tools with a test input, printing the JSON response.

## Scenario
Meridian's security team wants to give their AI assistant access to live data — not training
data, but the actual alert database and incident records. Your job: build an MCP server with
three tools and confirm that the tool-call protocol works as specified before wiring it to
a model in Module 06.

> Everything runs locally against bundled seed data. No external targets, no authorization needed.

## Do

1. [ ] `make demo` and read the output for all three tools. For each tool call, identify:
   - The **tool name and arguments** sent in the request
   - The **JSON response** returned
   - Whether the output is machine-parseable (can Python `json.loads()` it?)

2. [ ] `make shell` and read `server/server.py`. Find:
   - How is the tool schema derived from the function signature?
   - What happens if `ioc` in `get_threat_intel` contains a SQL-injection-style string
     (e.g. `'; DROP TABLE iocs; --`)? Does the function sanitise it?
   - Does `search_alerts` handle an empty result set without crashing?

3. [ ] Add a fourth tool to `server/server.py`:
   ```python
   @mcp.tool()
   def list_open_incidents() -> dict:
       """List all open incidents from the Meridian incident database.
       Returns a list of incident IDs, titles, and severity levels."""
       ...
   ```
   Implement it using `data/incidents.json`. Run `make demo` and confirm the new tool
   appears in the tool list and returns valid JSON.

4. [ ] Write a test client (`scripts/test-client.py`) that:
   - Connects to the MCP server
   - Calls `tools/list` and prints the tool names and descriptions
   - Calls each tool with a test argument and prints the result

5. [ ] Review the tool descriptions in `server/server.py`. For each tool, ask: is the
   description precise enough that a model could use it correctly without asking a follow-up
   question? Improve any description that's vague. Document your changes in a comment.

## Success criteria — you're done when
- [ ] `make demo` calls all three original tools and prints valid JSON for each.
- [ ] Your fourth tool (`list_open_incidents`) is implemented and appears in the demo.
- [ ] `scripts/test-client.py` exists and successfully calls `tools/list`.
- [ ] At least one tool description has been improved with a comment explaining why.

## Deliverables
`server/server.py` (with the fourth tool) + `scripts/test-client.py`. Commit both.

## Automate & own it
**Required.** Add input validation to `get_threat_intel` and `search_alerts`:
- `get_threat_intel`: reject `ioc` strings longer than 255 characters or containing characters
  outside `[a-zA-Z0-9./:-_@]`. Return an error dict, not a Python exception.
- `search_alerts`: reject empty query strings; limit results to 20 items.
Have a model draft the validation logic; you verify it handles the edge cases (Unicode, null
bytes, excessively long strings). Commit the validated server.

## AI acceleration
Paste the `server.py` code into a frontier model and ask it to review the tool descriptions
for clarity. Then compare its suggestions to your own improvements. Where does it identify
vagueness you missed? Where is its suggested language imprecise for a security context?

## Connects forward
The MCP server you build here is the data layer for the SoC Copilot in Module 06 — the
model will call these tools at inference time to answer live questions. Module 09 will
demonstrate how a malicious IOC string in `search_alerts` can inject into the model's
context and manipulate its behaviour.

## Marketable proof
> "I can build MCP servers with Python using fastmcp — exposing security data as typed,
> schema-validated tools that any MCP-compatible AI client can call, with input validation
> and access control built into the server."

## Stretch
- Implement a `require_confirmation` decorator that wraps any tool marked as action-taking:
  the tool prints a confirmation prompt and waits for explicit approval before executing.
  Apply it to a hypothetical `isolate_host(hostname)` stub.
- Add HTTP Bearer token authentication to the MCP server (fastmcp supports this). Test that
  calls without the token return a 401 error.
