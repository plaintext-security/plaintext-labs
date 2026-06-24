# Lab 03 — Structured Data & Reporting

> **Lab environment: real-data rewire — validation deferred.** `data/alerts.json` is now real Suricata `eve.json` alerts from a public PCAP (WRCCDC-2018) instead of synthetic records. `make up && make demo && make down` has **not** yet been re-run on a clean Linux runner against this change; validate before marking the lab done.

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/03-structured-data-reporting
make up        # Python 3.12 container with rich installed
make demo      # runs report.py over data/alerts.json
make shell
make down
```

`data/alerts.json` is a set of **real Suricata `eve.json` alert records** — the output of running
the Suricata IDS over a real public packet capture (the WRCCDC-2018 / Western Regional Collegiate
Cyber Defense Competition network capture). A small offline **fallback** set ships committed in the
repo so the lab works with no network; run `make fetch` to pull the full real export over the
network (see `data/PROVENANCE.txt` for source URL and retrieval date).

Each record is a JSON object with top-level `timestamp`, `src_ip`, `dest_ip`, `dest_port`, `proto`,
and a nested `alert` object holding `signature`, `category`, and `severity`. **Suricata severity is
an integer where lower = more urgent (1 = highest, 2 = medium, 3 = low).** Real exports are messy:
some records share a fingerprint (duplicates) and some are **missing the nested `severity` field
entirely** — exactly the edge cases your code must survive.

## Scenario
A Suricata sensor exported a JSON dump of alerts (`eve.json`). The team wants a morning briefing
that is: (a) deduplicated — the same signature firing on the same source/dest counts as one; (b)
filtered by severity; (c) available as a CSV for the ticket system; and (d) readable as a terminal
table for the analyst on call. Build `report.py` to do all four.

> Everything runs locally against bundled real data. No authorization issues.

## Do
1. [ ] Read `data/alerts.json` with `json.load()`. Print the total record count and the count of
   unique `alert.signature` values. (This is your sanity check before you process anything.)
2. [ ] Deduplicate: define a fingerprint as `(alert.signature, src_ip, dest_ip, dest_port)`.
   Use a `set` to remove duplicates. How many records remain?
3. [ ] Filter by severity. Remember Suricata's integer scale (1 = highest, 3 = lowest) — keep
   records at or below a max-severity threshold, and map the int to a label (1→HIGH, 2→MEDIUM,
   3→LOW) for the report. Use `.get()` on the nested `alert` object so records **missing** the
   `severity` field are silently skipped rather than crashing.
4. [ ] Write the filtered, deduplicated alerts to `output/report.csv` using `csv.DictWriter`.
   Columns: `timestamp`, `severity`, `signature`, `category`, `src_ip`, `dest_ip`, `dest_port`,
   `proto`.
5. [ ] Render a `rich` table to the terminal: one row per alert, severity colour-coded (HIGH =
   red, MEDIUM = yellow). Print a summary line below: total raw alerts → kept (deduplicated).
6. [ ] Handle the edge case: some records have **no** `severity` field under `alert`. Confirm your
   script skips them without raising a `KeyError` or `TypeError`.

## Success criteria — you're done when
- [ ] `report.py` exits 0 and produces `output/report.csv`.
- [ ] The CSV has the correct headers and no duplicate rows.
- [ ] The terminal table colour-codes severity correctly.
- [ ] Records missing the `severity` field are skipped without crashing.
- [ ] The deduplication count matches what you calculated by hand for a small sample.

## Deliverables
`report.py` + `output/report.csv`. Commit `report.py`; do not commit `output/` (add it to
`.gitignore`). The data file stays in `data/`.

## Automate & own it
**Required.** Add a `--max-severity` flag to `report.py` so the caller can set the severity
threshold from the command line (e.g., `python report.py --max-severity 1` to keep only HIGH).
Have a model draft the `argparse` wiring; check that validation fails gracefully on an out-of-range
or non-integer value (e.g., `--max-severity 9` or `--max-severity BANANA`) and that the default
behaviour is unchanged. Commit the updated script.

## AI acceleration
Ask a model to generate `report.py` from this lab description. Run it. Then deliberately feed it
the records that are **missing** the nested `severity` field and the duplicate records — does it
handle them? Where does it crash or silently misbehave? Fix those cases yourself and document the
fix in a comment. The model's first draft is a time-saver; the version that handles real eve.json
data is yours.

## Connects forward
The JSON → filter → deduplicate → report pattern is the skeleton of every alert-enrichment
pipeline you will build. Module 04 adds API calls between filter and report (enriching IPs
before writing the CSV); module 07 adds web scraping as an additional data source.

## Marketable proof
> "I process structured security data in Python — JSON in, filtered and deduplicated, CSV and
> rich terminal table out — with defensive field access so real-world messy data doesn't crash
> the pipeline."

## Stretch
- Add a summary bar chart rendered in the terminal using only `rich.progress.BarColumn` (no
  matplotlib) — one row per severity level showing relative count.
- Read from stdin instead of a file (`json.load(sys.stdin)`) and test it with
  `cat data/alerts.json | python report.py`.
