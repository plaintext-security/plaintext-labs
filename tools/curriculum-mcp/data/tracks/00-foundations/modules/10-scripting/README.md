# Module 10 — Scripting & Automation

*Type 9 · Tool-Build — the product is a reusable tool others run, not a throwaway script (the track's automation spine). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *analysts don't script for fun. They script when the data outgrows the eyes.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~5–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules (esp. 04 Linux, 08 Encoding)
{ .module-meta }


## The scale problem

In earlier modules you did things by hand: you decoded a base64 blob, you read an `auth.log` and
named the IP brute-forcing the box, you eyeballed a few lines and rendered a verdict. That works at
ten lines. It does not work at ten thousand.

Look at almost any real [CISA advisory](https://www.cisa.gov/news-events/cybersecurity-advisories)
and scroll to the indicators section: it ships a table — sometimes a separate machine-readable file —
of **IOCs** (*indicators of compromise*: IP addresses, domains, file hashes a defender should hunt
for). A single advisory can list hundreds. A web or auth log on a busy server is tens of thousands of
lines a day. You are not going to find the one malicious line, or cross-reference 300 hashes against
your fleet, by *reading*. The data has outgrown your eyes.

That's the honest reason analysts script. Not because typing Python is fun — because **a human cannot
reliably do a boring thing ten thousand times, and a computer cannot do anything else.** The whole job
of this module is to take one analysis you already did by hand and turn it into a small tool that does
it a thousand times, the same way, every time.

The flip side of that power wrote the opening chapter of network security. On 2 November 1988, a
Cornell graduate student released the [Morris worm](https://st.llnl.gov/news/look-back/1988-morris-worm-internets-first-cyberattack):
a single self-replicating program that spread by *automating* a handful of Unix exploits, and within
hours had hit an estimated **6,000 of the roughly 60,000 computers then on the Internet** — about a
tenth of it. Nobody attacked 6,000 machines by hand; one script did, at machine speed. That is the same
lever you are about to pick up — the only difference between the worm and your IOC-hunting tool is which
side of the keyboard the automation serves. Scale cuts both ways, and that is exactly why a defender has
to script too.

## The mental model: build a tool, not a throwaway

A good security script is not an "application," but it is also not a one-off you paste into a terminal
and lose. It is one boring decision, written down so it can be re-run *by other people*: **read input →
parse → filter → output a clean result.** Four pieces of Python's standard library cover almost all of
it — `pathlib` (read a file), `re` (pull a field out of messy text with a regular expression),
`collections.Counter` (tally), `argparse` (take options from the command line). You will not become a
software engineer here, and you don't need to.

The distinction this module turns on is **tool vs. throwaway.** A throwaway runs once, on your machine,
with the path hard-coded, and dies when you close the terminal. A *tool* is the same logic packaged so a
teammate can pick it up cold: it takes its input as a flag (`--threshold`, `--json`) instead of an edited
line, it answers `--help`, it ships a short README that says what it does and how to run it, and it has at
least one basic test that proves it still gives the right answer when you change it later. That packaging
is not bureaucracy — it is the difference between a result you got once and a *capability you own and can
hand off*. Everything the automation track later compounds on is this construct: a reusable, reviewable
tool, not a pile of scratch scripts.

Two ideas make a script worth writing, and both are about trust:

**A script is a hypothesis you can re-run.** When you say "the brute force is coming from one IP,"
that's a claim. A script makes the claim *checkable* — run it again, on tomorrow's log, and it either
holds or it doesn't. Manual analysis evaporates the moment you close the terminal; a script is the
analysis, preserved.

**A script is a teammate can read.** The point isn't only that the computer runs it — it's that
another analyst (or you, in six months) can open the file and see *exactly* what you counted and what
you ignored. So you automate the **toil** — the find-and-tally, the decode-this-blob, the
extract-every-IP — and you keep the **judgment** for yourself. The script flags 50 IPs over a
threshold; *deciding which are the attacker and which are your own backup job* is still your call, and
it should be. A tool that quietly makes judgments for you is worse than no tool, because you'll trust
it.

## The review skill (this is the main event)

Here's the thing that makes this a *security* lesson and not a Python lesson: **a model will write the
whole script for you in five seconds, and it will look right.** From here on, your job is not typing —
it's *reviewing*. This is the first real rep of the posture the entire rest of the curriculum assumes:
**AI authors → you review every line → you own it.**

AI-generated parsing code fails in quiet, specific ways, and you have to learn to see them:

- **The wrong assumption about the data.** The model writes a regex for the log format it *imagined*,
  not the one you have. It runs without error and matches *nothing* — or matches the wrong field.
- **The silent failure.** A line it can't parse gets skipped with no warning, so your "top 10 IPs" is
  quietly missing the half of the log that didn't fit the pattern. The output looks clean and is wrong.
- **The off-by-one and the edge case.** It counts the header row. It mishandles the last line with no
  newline. It treats `10.0.0.1` and `10.0.0.1 ` (trailing space) as two different IPs.

You catch these by *running it against data you understand* — feed it the ten lines you already
analyzed by hand and confirm it gets your answer — and by deliberately feeding it a malformed line to
see what it does. **If you can't explain every token in the regex, you don't own the script yet; you're
just pasting.** Owning it is the deliverable.

## Learn (~3–4 hrs)

**Python, fast — for people who haven't written one**
- [Python's own tutorial — sections 3, 4, 6, 7](https://docs.python.org/3/tutorial/) (~90 min) — the official starting point: variables, `if`/`for`, functions, reading files. Type along; skip the rest for now.
- [Automate the Boring Stuff with Python (free online)](https://automatetheboringstuff.com/) — Al Sweigart's classic; read the **Functions**, **Reading and Writing Files**, and **Designing and Deploying Command Line Programs** chapters — the security-automation core.

**The four modules a security script actually uses**
- [`re` — regular expressions](https://docs.python.org/3/library/re.html) (reference) — the analyst's scalpel for pulling one field out of messy text; you'll reach for it on every log-parsing task.
- [`argparse` tutorial](https://docs.python.org/3/howto/argparse.html) (~30 min) — how a script takes options (`--threshold`, `--json`) from the command line, like every real CLI tool.
- [Real Python — Regular Expressions in Python](https://realpython.com/regex-python/) (~40 min) — the `re` module done properly, with worked examples.
- [regex101](https://regex101.com/) (tool) — build and test your pattern interactively (set the flavour to Python) *before* it goes into code. This is where you catch the "matches nothing" bug.

**The data, for real**
- [CISA Cybersecurity Advisories](https://www.cisa.gov/news-events/cybersecurity-advisories) — open one recent advisory, find its indicators/IOC section, and see the scale problem with your own eyes before you write a line of code.
- [The 1988 Morris Worm — LLNL "Look Back"](https://st.llnl.gov/news/look-back/1988-morris-worm-internets-first-cyberattack) (~10 min) — the short, primary-source history of the first automation-at-scale attack: one self-replicating program, ~6,000 of ~60,000 hosts in a day. Read it for the lever — the same automation you'll wield as a defender.

## Key concepts
- You script when the data outgrows the eyes — not for fun, for scale and repeatability
- Automation-at-scale is the whole game on both sides — the Morris worm hit ~6,000 hosts in a day with one self-replicating script; defenders script for the same reason
- The shape of a security tool: **read → parse → filter → output**
- The four-piece standard library: `pathlib`, `re`, `collections.Counter`, `argparse`
- **Tool, not throwaway:** flags (not hard-coded paths), a `--help`, a short README, one basic test — so another person can run it
- A script is a re-runnable hypothesis and a readable artifact a teammate can audit
- Automate the toil; keep the judgment — never let the tool decide *which* result matters
- Reviewing AI code: wrong data assumption, silent failure, off-by-one — caught by running against data you understand

## AI acceleration
This module *is* the AI-acceleration lesson, so do it deliberately: have a model draft the whole
parser, then refuse to trust it. Run it against the ten lines you already analyzed by hand and confirm
it reproduces your answer. Feed it a malformed line and watch what it does — does it warn, or silently
drop it? Read the regex token by token and predict what it matches before you run it. The skill that
transfers to every later track is not "prompt a model to write code" — it's catching the off-by-one,
the wrong assumption, and the silent skip that make confident, wrong output. Typing was never the
skill. Directing and reviewing it is, and you own what you ship.
