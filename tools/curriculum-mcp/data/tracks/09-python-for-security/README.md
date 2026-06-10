# Track 09 — Python for Security

**Build your own tools.** Most security work is one good script away from automated. This
track turns you from someone who *runs* tools into someone who *writes* them — and who can
direct and review the ones AI writes.

## What you'll be able to do
- Parse, enrich, and reshape security data confidently.
- Talk to APIs and security tools programmatically.
- Build usable CLI tools and a security-focused MCP server.
- Review and own AI-generated code instead of pasting it blindly.

## Modules

| # | Module | What you'll learn | OSS tools |
|---|--------|-------------------|-----------|
| 01 | [Setup & Security Idioms](modules/01-setup-idioms/README.md) | A clean, repeatable Python toolchain | `python3`, `venv` |
| 02 | [Files, Regex & Log Parsing](modules/02-files-regex-parsing/README.md) | Extracting signal from raw logs | `re`, `pathlib` |
| 03 | [Structured Data & Reporting](modules/03-structured-data-reporting/README.md) | JSON/CSV in and out; readable output | `json`, `csv`, `rich` |
| 04 | [HTTP & APIs for Enrichment](modules/04-http-apis-enrichment/README.md) | Querying threat-intel and tool APIs | `requests`, `httpx` |
| 05 | [Building CLI Tools](modules/05-building-cli-tools/README.md) | Real tools with arguments and help | `argparse`, `typer` |
| 06 | [Network Programming](modules/06-network-programming/README.md) | Sockets and packet crafting | `socket`, `scapy` |
| 07 | [Automating the Web](modules/07-automating-the-web/README.md) | Responsible scraping and session handling | `requests`, `beautifulsoup4` |
| 08 | [Driving Security Tools](modules/08-driving-security-tools/README.md) | Wrapping VirusTotal, MISP, and friends | `requests`, `pymisp` |
| 09 | [Building an MCP Server](modules/09-building-mcp-server/README.md) | Exposing a tool to an LLM | `fastmcp` |
| 10 | [Packaging, Testing & Owning AI Code](modules/10-packaging-testing/README.md) | Reviewing, testing, and shipping | `pytest`, `ruff` |

## Prerequisites
Complete Track 00 — Foundations (module 10 — Scripting & Automation).

## Capstone
Build a small but genuinely useful security tool — for example, an IOC enrichment CLI or an
MCP server that exposes a tool to an LLM — with tests and a README. **Deliverable:** the
tool, its tests, and a short write-up of what you had AI write and what you changed.

## AI & automation
This is the track where "AI authors → you review → you own it" becomes a daily habit. A
model will write the whole script; your job is to read it — check the regex, handle the
malformed input, confirm it does nothing unintended — then test it and own it. The
competency isn't typing the code; it's directing and reviewing it.

## Standards & further reading
- Python standard library and PEP 8
- OWASP Secure Coding practices
- The Model Context Protocol specification (modelcontextprotocol.io)
