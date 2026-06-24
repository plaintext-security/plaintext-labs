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

## Phases & projects

The ten modules run in three phases; each ends in a **project** that integrates its modules (a phase
is the substantial, standalone unit — a single module is a few hours). Each project carries the
"AI authors → you review → you own it" habit into committed, tested code.

- **Phase 1 · Parse & report** (01–03) — **Project:** a log-analysis script with a clean toolchain
  that parses a real log with regex, reshapes it through structured data, and emits a readable
  JSON/CSV plus a `rich` console report — with tests on the parsing.
- **Phase 2 · Talk to the network & the world** (04–07) — **Project:** an IOC enrichment CLI (with
  `typer`/`argparse`) that queries threat-intel APIs, plus a small network or scraping tool — error
  handling, rate limits, and responsible use built in.
- **Phase 3 · Tooling, MCP & shipping** (08–10) — **Project:** the track capstone — wrap a security
  tool (VirusTotal/MISP) and expose it to an LLM as an MCP server, then package it with `pytest`/`ruff`
  and a README — delivering the tool, its tests, and a write-up of what AI wrote vs. what you changed.

## Prerequisites
Complete Track 00 — Foundations (module 10 — Scripting & Automation).

## Capstone
Build a small but genuinely useful security tool — for example, an IOC enrichment CLI or an
MCP server that exposes a tool to an LLM — with tests and a README. **Deliverable:** the
tool, its tests, and a short write-up of what you had AI write and what you changed.

The starter scaffold and acceptance checks live in
[`plaintext-labs/python-for-security/capstone/`](https://github.com/plaintext-security/plaintext-labs/tree/main/python-for-security/capstone).

### Capstone rubric

It must be a **genuinely useful tool you own** — tested, documented, reviewed line by line, and
**fed real data, not synthetic stand-ins** (a free threat feed like abuse.ch URLhaus/Feodo, a
public log/PCAP corpus, or a real CVE record). **Proficient is the bar to ship.**

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Usefulness** | A toy that re-implements a one-liner | Solves a real security task (enrichment, parsing, an MCP tool) you'd actually reach for | Fills a real gap; handles a workflow start to finish |
| **Code quality** | Monolithic script; no error handling | Structured, handles malformed input, passes `ruff`; has a `--help` | Idiomatic, typed, packaged installable; clean separation of concerns |
| **Tests** | None, or they only test the happy path | `pytest` covering core logic *and* edge/malformed input | Meaningful coverage incl. failure modes; tests run in CI |
| **Robustness** | Crashes on bad input or API errors | Fails gracefully; rate-limits/retries where it talks to APIs | Handles secrets safely (env, not hardcoded); no injection of unvalidated input |
| **Real data** | Toy/synthetic inputs the tool invents | **Required:** consumes a real feed or dataset (e.g. abuse.ch URLhaus/Feodo, a public log/PCAP corpus, a real CVE/NVD record), with provenance noted | Wires the tool to a live feed with a cached offline fallback so it runs with no network |
| **Ownership of AI code** | Pasted AI output unread | Write-up names what AI generated and what you changed and why | Demonstrates a caught bug/risk in the generated code that you fixed and explained |

## AI & automation
This is the track where "AI authors → you review → you own it" becomes a daily habit. A
model will write the whole script; your job is to read it — check the regex, handle the
malformed input, confirm it does nothing unintended — then test it and own it. The
competency isn't typing the code; it's directing and reviewing it.

## Standards & further reading
- Python standard library and PEP 8
- OWASP Secure Coding practices
- The Model Context Protocol specification (modelcontextprotocol.io)
