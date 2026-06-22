# Lab 10 — Build the Tool: A Reviewable Log Parser in Python

*Type 9 · Tool-Build — the deliverable is a packaged, reviewable tool others can run. [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo.

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/10-scripting
make up      # build a Python 3.12 container (mounts your working dir)
make demo    # show the target output + the Python building blocks
make shell   # interactive shell with data/ mounted
make down    # stop when done
```

Your working directory is mounted into the container — write `topips.py` here and it persists on your
host. The lab ships a **real-format SSH `auth.log`** under `data/`: genuine
[T1110 Brute Force](https://attack.mitre.org/techniques/T1110/) noise, the same shape you triaged by
hand in module 04 — now at a scale you wouldn't want to count by eye.

## Scenario

You're triaging a host. The `auth.log` is full of failed-login lines and you need the one answer that
matters: **which source IPs are hammering this box, ranked by how hard.** You did this for ten lines by
hand already. Now you build the tool that does it for ten thousand — the triage script you'll write a
hundred variations of, and the first piece of your Foundations capstone toolkit.

This is **build-first**: the deliverable is the script. Everything below is about building it *and being
able to defend every line of it* — especially if AI wrote the first draft.

## Do

You may have a model draft each step — but **read every line before you keep it**, and run it against
data you understand. Don't paste blind.

1. [ ] **See the scale problem.** `wc -l data/ssh_auth.log`, then `grep "Failed password"` it. Confirm
   for yourself that ranking these by hand is not happening. Run `make demo` to see the target output
   your tool should reproduce.

2. [ ] **Read input.** Write `topips.py` that opens the log and iterates its lines. (Building block:
   `pathlib.Path(path).read_text().splitlines()`.) Print the line count to prove it read the file.

3. [ ] **Parse — pull the IP out with a regex.** Each failed-login line contains
   `Failed password for <user> from <IP> port <N>`. Write a regex that captures the IP, and *test it in
   [regex101](https://regex101.com/) (Python flavour) first.* (Building block: `re.compile(...)` +
   `.search(line)`; `\S+` matches a run of non-space characters.) Confirm it captures the IP from one
   line you read with your own eyes.

4. [ ] **Filter & tally.** Count failed-login attempts per source IP. (Building block:
   `collections.Counter` — `counts[ip] += 1`.)

5. [ ] **Output a clean result.** Print the IPs ranked by count, highest first. (Building block:
   `Counter.most_common()`.)

6. [ ] **Handle the line you can't parse — on purpose.** Feed it a deliberately malformed line. Decide
   what the *right* behaviour is (skip it but **count how many you skipped** and warn — never drop data
   silently), and make it do that. This is the silent-failure bug from the README; close it.

7. [ ] **Defend it.** Re-read the regex token by token. Be able to say what every piece matches and what
   it would *miss* (IPv6? a different log format? a trailing space?). If you can't, you don't own it yet.

8. [ ] **Package it as a tool, not a throwaway.** Make it run for someone who isn't you: take the log path
   and threshold as `argparse` flags (no hard-coded paths), make `--help` describe what it does, write the
   short `README.md`, and add **one basic test** — even a three-line check that, given a tiny fixture log
   with a known answer, the tool returns that answer. That single test is what lets you change the tool
   later and trust it still works.

## Success criteria — you're done when
- [ ] The tool prints a ranked count of source IPs from the sample.
- [ ] On a line it can't parse it does something sensible — it does not crash, and it does not *silently*
  drop the line (it tells you how many it skipped).
- [ ] You can explain every token in the regex, and name one input shape it would miss.
- [ ] Its output matches your by-hand answer on a handful of lines you checked yourself.
- [ ] It runs for someone who isn't you: input/threshold are **flags**, `--help` works, a short README
  exists, and **one basic test passes** against a known-answer fixture.

## Deliverables
The **packaged tool**: `topips.py` (with `argparse` flags and a working `--help`), a one-paragraph
`README.md` (what it does, how to run it, and **one limitation you'd fix next** — naming the limitation is
part of owning it), and **one basic test** (`test_topips.py`, or a documented manual check) proving it
returns the known answer on a small fixture. Commit all three. Do **not** commit the real log file or any
captured host data — reference the dataset, don't vendor it (a tiny known-answer fixture for the test is
fine to commit).

## Automate & own it
**Required — this is the whole module.** `topips.py` *is* your artifact. To prove it's a tool and not a
one-off, have a model extend it with `argparse`: a `--json` flag (emit machine-readable output another
tool could consume) and a `--threshold N` flag (only show IPs at or above N attempts). Then **review the
diff line by line before you keep a character of it** — does the threshold use `>=` or `>` (off-by-one)?
Does `--json` still report the skipped-line count? Does it break on an empty file? AI drafts, you review
every line, you own it. The reviewed, defended script is your deliverable.

## AI acceleration
Ask a model to write the parser from scratch, then audit it as an adversary: feed it the lines you
already analyzed by hand and confirm it gets *your* answer; feed it a malformed line and watch whether
it warns or silently skips; read the regex and predict its matches before running. Catching the wrong
assumption and the silent skip is the transferable skill — far more than generating the code.

## Connects forward
This is the **automation spine** of Foundations. The read→parse→filter→output shape and the AI-review
habit run straight into module 11 (a pre-commit secret-scan hook is the same pattern) and the **capstone
toolkit** (decode a blob, check a hash, parse a log — all reviewable scripts you own). It's also the
on-ramp to the offensive and defensive tracks' Python-for-security and detection-engineering work.

## Marketable proof
> "I turn repetitive triage — log parsing, IOC extraction, ranked output — into small, reviewable Python
> tools, and I can audit and harden AI-generated code instead of pasting it blind. I know the difference
> between automating the toil and automating the judgment."

## Stretch
- Point a *second* script at a real [CISA advisory](https://www.cisa.gov/news-events/cybersecurity-advisories)'s
  IOC list: read the indicators, extract every IP/domain/hash, and emit a clean deduplicated list — the
  scale problem from the README, solved end to end.
- Let `topips.py` read from `stdin` too, so it composes in a pipeline (`grep Failed auth.log | python3 topips.py`).
