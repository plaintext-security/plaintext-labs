# Module 10 — Scripting & Automation

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *stop doing by hand what a 20-line script does reliably.*

## Why this matters
Security work is repetition: parsing logs, enriching indicators, calling APIs, reshaping
data. Python is the field's lingua franca because its standard library already covers most
of it. You won't become a software engineer here — you'll learn to automate the boring 80%
so your attention goes to the 20% that needs judgment. It's also where the *AI authors →
you review → you own it* habit begins, because a model will write the script and you have
to read it.

## Objective
Turn a repetitive analysis task into a small, repeatable, reviewable Python tool.

## The core idea
Security work is repetition — parsing logs, enriching indicators, calling APIs, reshaping data — and
Python is the field's lingua franca because its standard library already covers most of it. The goal
here is explicitly *not* to become a software engineer; it's to automate the boring 80% so your
attention goes to the 20% that needs judgment. The mental model is "small, repeatable, reviewable
tool," not "application": read a file, extract with regex, reshape JSON, maybe call an HTTP API, print
the answer. Four standard-library modules (`re`, `json`, `pathlib`, `argparse`) cover most of it.

Regex earns its own mention — it's the analyst's scalpel for pulling the one field you want out of
messy text, and it recurs in every log-parsing, detection, and triage task across the curriculum, so
it's worth real practice (build and test patterns in regex101 before they go into code).

The judgment, and where a curriculum-wide habit is born: **a model will happily write the whole
script**, so your job shifts from *typing* to *reviewing* — check the regex actually matches, confirm
it handles the malformed line, verify it does nothing unintended — then own it. This is the first
concrete rep of **AI authors → you review → you own it**, the posture every later track assumes. Typing
the code was never the skill; directing and reviewing it is.

## Learn (~4 hrs)

**Python, fast**
- [Automate the Boring Stuff with Python (free online)](https://automatetheboringstuff.com/) — Al Sweigart's classic; the files, regex, and command-line chapters are the security-automation core. Type along.
- [Corey Schafer — Python for Beginners #1: Install & Setup (~10 min)](https://www.youtube.com/watch?v=YYXdXT2l-Gg) — new to Python? start here, then continue his numbered beginner series as far as you need.

**Regex — the analyst's scalpel**
- [Real Python — Regular Expressions](https://realpython.com/regex-python/) — the `re` module done properly; you'll reach for this on every log-parsing task.
- [regex101](https://regex101.com/) — build and test your pattern interactively (set the flavour to Python) before it goes into code.

**Reference**
- [Python standard library — `re`, `json`, `pathlib`, `argparse`](https://docs.python.org/3/library/) — the modules a security script actually needs.

## Key concepts
- Reading files and iterating lines
- Regular expressions for extraction (`re`)
- Structured data: JSON in and out
- Functions and the `if __name__ == "__main__"` entry point
- Standard-library HTTP for enrichment

## AI acceleration
A model will happily write the whole parser. Your job is to read it — check the regex
matches, handle the malformed line, confirm it does nothing unintended — then own it.
Typing the code was never the skill; directing and reviewing it is.
