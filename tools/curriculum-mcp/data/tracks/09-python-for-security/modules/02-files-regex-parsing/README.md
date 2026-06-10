# Module 02 — Files, Regex & Log Parsing

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *logs are the ground truth; parsing them is the first craft.*

## Why this matters
Every security tool eventually outputs text: syslog lines, auth events, IDS alerts, firewall
drops. Before you can graph, alert, or escalate anything, you have to extract signal from that
text reliably. The analyst who can write a regex that plucks IPs from a noisy SSH auth log in
thirty seconds has a permanent edge over one who reaches for a GUI every time.

## Objective
Write a Python script that parses a realistic SSH authentication log, extracts failed-login IPs
with timestamps, identifies brute-force patterns, and outputs the top offenders — using only the
standard library (`re`, `pathlib`, `collections`).

## The core idea
Log parsing has two failure modes that look like success: the regex that matches *most* lines
(and silently drops the rest) and the one that matches *too broadly* (and pulls in noise that
looks like signal). The discipline is to write the regex against the actual format documented by
the application — not by eye-balling a few samples — then verify it on both a positive case and
a negative case before trusting the output. A parser that misses 5% of failed logins because of
a minor sshd format variation is worse than no parser, because you will believe the output.

`re` in Python is a full POSIX ERE dialect with named groups. Named groups — `(?P<name>...)` —
are the difference between a regex that produces a tuple of strings and one that produces a
dictionary you can reason about. Always use named groups for fields you intend to act on:
`(?P<ip>\d{1,3}(?:\.\d{1,3}){3})` is self-documenting; `(\d+\.\d+\.\d+\.\d+)` is a mystery
three months later. Compile the pattern once with `re.compile()` outside any loop — `re.match()`
called with a string literal inside a million-line loop recompiles on every call.

`pathlib.Path` is the modern replacement for `os.path` string manipulation. `Path("/var/log")`
gives you an object with `.name`, `.suffix`, `.read_text()`, `.glob()` — no more string
concatenation to build file paths. For large log files, iterate line-by-line (`for line in
path.open()`) rather than `.read_text().splitlines()` — the latter loads the entire file into
memory, which matters when sshd has been logging for a year.

Brute-force detection from logs is a counting problem: group failed-login attempts by source IP,
count them in a time window, and flag the ones that exceed a threshold. `collections.Counter` is
the right tool for the aggregate; a dictionary of `collections.deque` (with `maxlen=N`) is the
right tool for the sliding window. Neither requires a database — for a few thousand IPs, an
in-memory structure is fast enough and simpler to reason about. The moment your window needs
persistence across restarts, you add a database; don't add one before you need it.

## Learn (~2.5 hrs)

**Regex fundamentals (~1 hr)**
- [Regular Expressions HOWTO — Python docs](https://docs.python.org/3/howto/regex.html) — the canonical reference; the "Grouping" and "Non-capturing and Named Groups" sections are the ones to read carefully.
- [regex101.com](https://regex101.com/) — not a tutorial, but the fastest way to iterate on a pattern against a real log sample; paste a few lines and experiment.

**File handling (~30 min)**
- [pathlib — Object-oriented filesystem paths (Python docs)](https://docs.python.org/3/library/pathlib.html) — focus on `Path`, `read_text()`, `open()`, `glob()`; this replaces `os.path` for everything you'll do here.

**Collections for log analytics (~1 hr)**
- [collections — Container datatypes (Python docs)](https://docs.python.org/3/library/collections.html) — specifically `Counter` and `defaultdict`; these two handle 80% of the aggregation patterns in log analytics.

## Key concepts
- Named capture groups for self-documenting regex patterns
- `re.compile()` once; match in a loop — not the reverse
- `pathlib.Path` for portable, readable file operations
- Line-by-line iteration for memory-efficient log processing
- `Counter` for frequency analysis; sliding-window deque for time-windowed detection
- Verifying parsers on both positive and negative test cases

## AI acceleration
A model will write the regex for you instantly — and it will usually be subtly wrong on edge
cases (IPv6, lines with extra whitespace, slightly different sshd format versions). Give it a
sample of the actual log lines you're parsing, ask it to name the groups, then test its output
on at least five lines it has not seen. The validation step is the skill; the regex is just the
draft.
