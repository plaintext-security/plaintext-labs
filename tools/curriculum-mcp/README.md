# Curriculum MCP — point Claude/Cursor at Plaintext as a tutor

An [MCP](https://modelcontextprotocol.io/) server that exposes the **Plaintext curriculum**
(13 tracks, 158 modules, every Learn path and lab) to any MCP-compatible client — Claude
Desktop, Claude Code, Cursor — as tools, resources, and a tutor prompt. Wire it in and the
model can pull the *real* module text on demand instead of inventing it:

> "Walk me through the MCP servers module." · "What's the Learn path for web injection?"
> · "Find where the curriculum covers Kerberoasting." · "What should I study after RAG?"

This is a developer/learner tool, not a per-module lab — so it lives under `tools/`, not
`<track>/<module>/`. It is the dog-fooding companion to Track 12's
[*Building MCP Servers*](https://github.com/plaintext-security/plaintext/blob/main/tracks/12-ai-augmented-ops/modules/05-building-mcp-servers/README.md):
the same `FastMCP` pattern, pointed at the curriculum itself.

## What it exposes

**Tools** (the model calls these):

| Tool | Does |
|------|------|
| `list_tracks()` | The 13-track curriculum map. |
| `list_modules(track)` | Modules in a track, in order. Accepts `12`, `ai`, or `12-ai-augmented-ops`. |
| `get_module(ref)` | A module's concept — *Why this matters*, *Objective*, *The core idea*, *Key concepts*. |
| `get_learn_path(ref)` | The curated, grouped Learn resources (title, URL, why-line). |
| `get_lab(ref)` | The hands-on lab — scenario, ordered *Do* steps, deliverables. |
| `search_curriculum(query)` | Deterministic keyword search across every module and lab. |
| `suggest_next(ref)` | The next module in the same track. |
| `curriculum_stats()` | Counts: tracks / modules / labs / Learn resources. |

A `ref` is `<track>/<module>`, e.g. `12-ai-augmented-ops/05-building-mcp-servers`. Loose forms
resolve too: `ai/5`, `offensive/web`, `01-offensive/06`.

**Resources** (readable context): `curriculum://overview` (the whole map as Markdown) and
`curriculum://module/{track}/{module}` (a module's full README).

**Prompt**: `tutor(topic)` — a ready-made "be my Plaintext tutor, grounded in the tools" prompt.

## Architecture

```
curriculum-mcp/
├── server/
│   ├── curriculum.py     # pure-stdlib parser + index + search over tracks/  (no deps → testable offline)
│   ├── server.py         # the thin FastMCP layer: tools, resources, prompt
│   └── requirements.txt  # just `mcp` (the official MCP SDK)
├── data/tracks/          # committed snapshot of the curriculum Markdown (the zero-setup default source)
├── tests/
│   ├── smoke_test.py     # offline, dependency-free: parser + query layer (16 checks)
│   └── mcp_roundtrip.py  # spawns the server over stdio and drives it as an MCP client
├── examples/             # sample MCP client config
├── Dockerfile · docker-compose.yml · Makefile
```

The split is deliberate: **`curriculum.py` has zero third-party dependencies**, so the parsing,
indexing, and search can be compiled and smoke-tested with nothing but `python3` — the MCP SDK
is only needed to actually *serve*. Source defaults to the bundled `data/tracks/` snapshot; set
`CURRICULUM_DIR` to a full `plaintext/tracks` checkout to tutor over the latest, complete curriculum.

## Setup

### Run the validation (Docker)

```bash
cd tools/curriculum-mcp
make demo        # self-check + offline smoke test + MCP stdio round-trip, in the container
make test        # just the two test suites
```

### Run without Docker

```bash
cd tools/curriculum-mcp
make smoke              # dependency-free smoke test with your host python3 — no install
make test-local        # creates .venv, installs mcp, runs smoke + MCP round-trip
```

### Wire it into a client

MCP's default transport is **stdio**: the client launches the server as a subprocess and talks
over stdin/stdout. So you point the client at the `server/server.py` command rather than at a
running container.

1. Create a venv and install the SDK:
   ```bash
   cd tools/curriculum-mcp
   python3 -m venv .venv && .venv/bin/pip install -r server/requirements.txt
   ```
2. Add the server to your client, editing the absolute paths (see
   [`examples/claude-desktop-config.json`](examples/claude-desktop-config.json)):
   - **Claude Desktop** — merge the `mcpServers` block into `claude_desktop_config.json`.
   - **Cursor** — same block into `.cursor/mcp.json`.
   - **Claude Code** —
     ```bash
     claude mcp add plaintext-curriculum -- \
       /ABS/PATH/tools/curriculum-mcp/.venv/bin/python \
       /ABS/PATH/tools/curriculum-mcp/server/server.py
     ```
3. Restart the client and ask it to "use the plaintext-curriculum tools to tutor me."

To tutor over a live, full curriculum instead of the bundled snapshot, set
`CURRICULUM_DIR=/path/to/plaintext/tracks` in the server's `env`.

## Validation

All three layers are validated and green (Python 3.12, `mcp` 1.27):

- `python3 server/server.py --selfcheck` → `{"ok": true, "tracks": 13, "modules": 158, "labs": 158, "learn_resources": 691}`
- `tests/smoke_test.py` → 16 checks dependency-free (20 with the server layer when `mcp` is present)
- `tests/mcp_roundtrip.py` → a real MCP client connects over stdio, lists all 8 tools + the
  resource template + the `tutor` prompt, calls tools, and reads a resource.

## Notes

- **Read-only.** The tutor only reads the curriculum; no tool writes or takes action, so there
  is no action-taking trust boundary to guard (unlike Track 12 Module 05's `isolate_host`-style
  tools). Inputs are bounded (refs / search terms) and the snapshot is read-only.
- **Snapshot freshness.** `data/tracks/` is a committed copy and will drift from the live
  curriculum; see [`data/README.md`](data/README.md) to refresh it or override the source.

## License

Code under [LICENSE-CODE](../../LICENSE-CODE) (MIT); the bundled curriculum text under the
Plaintext content license (CC BY 4.0).
