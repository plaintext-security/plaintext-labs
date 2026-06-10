# Module 05 — Building CLI Tools

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *a tool that takes arguments and has a `--help` is a tool someone else can use.*

## Why this matters
A script with hardcoded paths and no usage string is a personal tool. A CLI with documented
arguments, sensible defaults, `--help` output, and clean error messages is a team asset.
Most security tooling is command-line-first — that's the interface incident responders reach for
under pressure — and the difference between a script someone can use and one they have to modify
to run is the argument layer.

## Objective
Wrap the enrichment function from module 04 into a production-grade `ioc-check` CLI tool using
`typer`, with subcommands, typed arguments, `--help` output, and clear error messages for bad
input.

## The core idea
There are two generations of Python CLI tools: `argparse` (standard library, explicit, verbose,
but always available) and `typer` (third-party, based on type annotations, generates help text
automatically, much less boilerplate). Both are correct choices; `typer` is the modern default
for new tools because the function signature *is* the argument parser — you add a type hint, and
`typer` adds the validation, the help text, and the error message automatically.

The design principle for security CLI tools is: **be explicit about failure modes, never silent.**
If an argument is missing, say what is missing. If a file doesn't exist, say the file path and
why. If the API returns an error, print the status code and the URL. A tool that exits with `1`
and an unhelpful empty error message is harder to debug than one that exits with `1` and `"API
returned 429 for 8.8.8.8 — you've hit the rate limit."` The extra line of error handling is an
hour saved the next time someone runs the tool in a hurry.

Exit codes matter. `0` = success; `1` = usage error or runtime failure. Any script that exits
`0` when it failed silently is a lie to the caller. In shell pipelines and CI jobs, exit codes
are the interface — a failed enrichment that exits `0` will not fail the CI gate that runs it.
Use `raise typer.Exit(code=1)` or `sys.exit(1)` explicitly; do not rely on exceptions propagating
to the top level and causing a non-zero exit by accident.

Subcommands are the pattern for tools that do related but distinct things: `ioc-check enrich
8.8.8.8`, `ioc-check report --input enriched.json`, `ioc-check version`. `typer` handles this
with `app.command()` decorators. Keep subcommands composable — each should read from files or
stdin and write to files or stdout, so they can be piped together in a shell one-liner. This is
the Unix philosophy applied to security tooling, and it is why `grep | awk | sort | uniq -c`
still beats most GUI dashboards for exploratory analysis.

## Learn (~2 hrs)

**Typer fundamentals (~1 hr)**
- [Typer — Build great CLIs (official tutorial)](https://typer.tiangolo.com/tutorial/) — work through the "First Steps", "CLI Arguments", "CLI Options", and "Commands" sections; this covers everything in the lab.

**CLI UX for security tools (~30 min)**
- [Command Line Interface Guidelines — clig.dev](https://clig.dev/) — the best single reference for CLI design; read the "Basics", "Output", and "Errors" sections; this is what separates a frustrating tool from a well-designed one.

**argparse (the standard library fallback) (~30 min)**
- [argparse — Parser for command-line options (Python docs)](https://docs.python.org/3/library/argparse.html) — focus on `add_argument`, `type`, `choices`, `required`, and `default`; you'll reach for this when you can't add third-party dependencies.

## Key concepts
- `typer` function signatures as the argument spec — type hints drive validation and help text
- Exit codes as the interface for shell pipelines and CI: `0` = success, `1` = failure
- Explicit error messages: what failed, which value, what to try
- Subcommands for related operations: `enrich`, `report`, `version`
- Reading from files or stdin, writing to stdout or files — composable by design

## AI acceleration
Ask a model to turn your `enrich.py` function into a `typer` app. It will get the basic
structure right instantly. Check the error handling: does it validate the IOC format before
calling the API? Does it exit `1` on API failure? Does the `--help` output actually describe
what the tool does? These three questions cover most of what makes a CLI tool usable under
pressure.
