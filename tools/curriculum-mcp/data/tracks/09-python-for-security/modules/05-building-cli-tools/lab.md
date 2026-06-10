# Lab 05 — Building CLI Tools

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/05-building-cli-tools
make up        # Python 3.12 container with typer + httpx installed; mock API running
make demo      # shows ioc-check --help and a sample enrich run
make shell
make down
```

The mock API from module 04 runs as a sidecar. The student container has `typer`, `httpx`, and
`rich` installed. `data/iocs.txt` is the same IOC list from module 04.

## Scenario
The Meridian enrichment script from module 04 works, but the rest of the team can't use it
without reading the source. Your task: wrap it into a proper CLI tool called `ioc-check` with
`--help` output, typed arguments, two subcommands (`enrich` and `report`), and clean error
messages. The tool should be runnable by anyone who can type `python ioc-check.py --help`.

## Do
1. [ ] From the scenario, sketch the CLI contract before writing code: which subcommands, which
   arguments and types, and what a good error message looks like for an invalid IOC type. (You'll
   diff your `--help` against the reference at the end with `make demo` — design it yourself first.)
2. [ ] Create `ioc-check.py` with two `typer` subcommands:
   - `enrich`: accepts `--ioc` (a single IOC string) or `--file` (a path to a list), and
     `--output` (optional path for JSON output; default stdout). Calls the mock API.
   - `report`: reads the JSON output from `enrich` and prints a `rich` table summary.
3. [ ] Add input validation to `enrich`: reject clearly invalid IOC formats (non-IP strings that
     aren't valid SHA-256 hashes) with a clear error message and exit code 1.
4. [ ] Confirm that `python ioc-check.py enrich --ioc 8.8.8.8` produces valid JSON output.
5. [ ] Confirm that `python ioc-check.py enrich --file data/iocs.txt | python ioc-check.py
   report` works end to end via stdin pipe.
6. [ ] Run `make demo` again — confirm your tool's `--help` output matches the reference shape.

## Success criteria — you're done when
- [ ] `python ioc-check.py --help` shows both subcommands with descriptions.
- [ ] `python ioc-check.py enrich --ioc 8.8.8.8` exits 0 and produces JSON.
- [ ] `python ioc-check.py enrich --ioc not-valid` exits 1 with a helpful error message.
- [ ] The `enrich | report` pipeline works end to end.

## Deliverables
`ioc-check.py`. Commit it. Do not commit generated output files.

## Automate & own it
**Required.** Add a `version` subcommand that prints the tool version from a `__version__`
variable. Then write a `test_cli.py` that uses `typer.testing.CliRunner` to test at least three
invocations: a valid single-IOC enrich, an invalid IOC (expects exit code 1), and `--help`
(expects exit code 0 and "enrich" in the output). Have a model draft the tests; run them with
`python -m pytest test_cli.py`; commit the test file.

## AI acceleration
Describe the tool's desired interface to a model and ask it to generate `ioc-check.py` with
`typer`. Then try to break it: call it with `--ioc ""` (empty string), `--file /nonexistent`,
and `--ioc 192.168.1.999`. Does it handle each case correctly? Fix what breaks and commit the
fix with a comment explaining what the model missed.

## Connects forward
`ioc-check` becomes the foundation for the MCP server in module 09 — the server exposes the
same `enrich` function as an LLM tool. The `typer` pattern reappears in every automation script
in Track 10.

## Marketable proof
> "I build security CLI tools with typer — typed arguments, --help output, composable
> subcommands, and clean exit codes so they work in shell pipelines and CI gates."

## Stretch
- Package `ioc-check` as a proper Python package with `pyproject.toml` so it installs via
  `pip install .` and runs as `ioc-check` (not `python ioc-check.py`).
- Add shell completion using `typer`'s built-in completion support.
