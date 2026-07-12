# Lab 05 — Wrap a Tool Without Opening a Shell

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/05-driving-tools-safely/`: the `sift` project, a couple of local
tools to wrap (`nmap`, `whois`), and a copilot-generated wrapper with a planted `shell=True` bug for the
review beat.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/05-driving-tools-safely
make up
make shell
make demo    # runs the safe wrapper and demonstrates the injection the unsafe one allows
make down
```

Reproducible at zero cost; everything runs locally against targets you control in the lab.

## Scenario

`sift` needs to enrich indicators by driving external tools. You'll build a safe subprocess wrapper into
it — then find and fix the command-injection hole in a copilot-generated version. The only targets are
ones you own inside the lab.

> Only test systems you own or have explicit written permission to test. Scan and shell out only against
> the lab's local targets.

## Do

1. [ ] **Find the planted injection.** You're handed a copilot-generated tool wrapper. Locate the
   `shell=True` command injection, and write down the *tell* that gave it away (the f-string interpolated
   into a shell string).
2. [ ] **Prove it's exploitable.** In the lab, pass an indicator like `x; id` (or `$(id)`) through the
   unsafe wrapper and observe the injected command run. This is why the review matters.
3. [ ] **Rewrite it safe.** Convert the wrapper to `subprocess.run([...], shell=False)` with an argument
   list. Confirm the same malicious indicator is now inert (passed as one literal argument).
4. [ ] **Validate before you shell out.** Add a boundary check (reuse Module 02's approach): the indicator
   must match its expected shape (domain/IP/hash) before any tool sees it. Reject the malformed.
5. [ ] **Parse structured output.** Drive the tool with a structured-output flag (e.g. `nmap -oX`) and
   parse that, not scraped stdout text.
6. [ ] **Automate & own it.** Commit the safe wrapper and the validation into `sift`, plus a one-line
   trust-checklist entry ("every `subprocess` call: `shell=False`, list args, validated input"). Note in
   the commit what the copilot got wrong and how you caught it.

## Success criteria — you're done when
- [ ] You found the planted `shell=True` injection and demonstrated it running an injected command.
- [ ] The rewritten wrapper uses `shell=False` with a list, and the same payload is now inert.
- [ ] Indicators are validated/allowlisted before any tool is invoked.
- [ ] The wrapper parses structured tool output, not scraped text.

## Deliverables
The updated `sift` repo: the safe tool wrapper, the input validation, the structured-output parser, and a
trust-checklist entry for reviewing `subprocess` calls. Do **not** commit scan output or any target data.

## AI acceleration
The module *is* an AI-review exercise: the vulnerable wrapper is exactly what a copilot ships. The skill
you're proving is catching `shell=True` on sight and reflexively rewriting to the list form — then
encoding that as a checklist so you (and your team) catch the next one. Have the copilot generate the
`nmap` wrapper fresh and check whether it reintroduces the bug; it often does.

## Connects forward
The safe, structured wrapper is what Module 06 exposes through both a `typer` CLI and a `FastAPI` service,
and what Module 08 red-teams once it's reachable by an LLM. The command-injection reflex transfers
directly to the Offensive track's injection modules — same bug, other side.

## Marketable proof
> "I wrap external security tools from Python without command-injection risk — `shell=False`, list args,
> validated input, structured-output parsing — and I catch the `shell=True` holes an AI copilot ships."

## Stretch (optional)
- Add a `bandit` (or `ruff` security-rule) CI check that fails the build on `shell=True`, so the class
  can't come back in.
- Wrap a second tool (`pymisp` or a VirusTotal query) behind the same safe pattern and share the
  validation.
