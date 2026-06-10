# Lab 02 — Files, Regex & Log Parsing

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/02-files-regex-parsing
make up        # Python 3.12 container
make demo      # runs the reference parse_log.py and shows top offending IPs
make shell     # interactive shell for development
make down
```

The container has only the standard library — no third-party parsing libraries. `data/sshd.log`
is 500 lines of realistic SSH authentication log from the fictional **Meridian Financial** jump
server: a mix of normal logins, failed password attempts, and a brute-force campaign from two
addresses.

## Scenario
Meridian's jump server generated an alert: "unusual authentication volume." You have the raw
`sshd.log`. Your task is to write a parser that extracts failed-login events by IP, identifies
any source that crosses a brute-force threshold (≥10 failures in any 60-second window), and
prints the top five offenders with failure counts — all with no external libraries.

> Everything runs locally against bundled data. No authorization issues.

## Do
1. [ ] Read `data/sshd.log` — identify the format of a "Failed password" line. What fields are
   present? Write down the regex pattern you'll use before writing any code.
2. [ ] Write `parse_log.py`:
   - Open `data/sshd.log` with `pathlib.Path` and iterate line by line.
   - Compile one regex with named groups: at minimum `ip`, `user`, and `timestamp`.
   - Count failures per IP with `collections.Counter`.
   - Print the top 5 IPs and their failure counts.
3. [ ] Extend the script to detect brute-force: flag any IP that has ≥10 failures within any
   60-second window. (Hint: parse the timestamp into a `datetime`; use a per-IP sorted list of
   times and a sliding pointer.)
4. [ ] Run `make demo` to compare your output with the reference solution. Do your top-5 IPs
   match? If not, check your regex against the log lines the reference catches that yours doesn't.
5. [ ] Write two short test cases in `test_parser.py` using only `assert`: one that confirms a
   known-bad line is parsed correctly, one that confirms a known-benign line returns `None`.

## Success criteria — you're done when
- [ ] `parse_log.py` runs cleanly and outputs the correct top-5 IPs.
- [ ] At least one IP is flagged as a brute-force source.
- [ ] Your regex uses named groups for all extracted fields.
- [ ] `test_parser.py` passes (run `python test_parser.py` — no framework needed yet).

## Deliverables
`parse_log.py` + `test_parser.py`. Commit both. The log file stays in `data/` — don't commit
any generated output files.

## Automate & own it
**Required.** Extend `parse_log.py` into a `watch_log.py` that accepts a `--log` argument and a
`--threshold` argument (default 10). Have a model draft the `argparse` or `typer` wiring; you
read and verify the argument handling, especially the default values and error messages for bad
input. Commit `watch_log.py`.

## AI acceleration
Give a model the first three lines of `sshd.log` and ask it for a named-group regex. Run the
result against five more lines — including the ones that look slightly different. Catch any that
it misses, fix the pattern, and document the edge case in a comment. The regex the model gives
you is a first draft; the version you tested is the production one.

## Connects forward
The parser pattern you build here — regex extraction → counter → threshold → alert — reappears
in module 07 (web scraping) and module 03 (structured reporting). In Track 02 (Defensive), the
detection-as-code module covers the same logic in Sigma; knowing the raw Python underneath makes
you a better Sigma author.

## Marketable proof
> "I parse security logs with Python — regex, named groups, standard-library aggregation — and I
> validate parsers against both positive and negative samples before trusting the output."

## Stretch
- Handle IPv6 addresses in the log (add `(?P<ip6>...)` as an alternative group).
- Write a `report.py` that reads the parser output and produces a simple histogram (use only
  `str.rjust` for alignment — no plotting libraries).
