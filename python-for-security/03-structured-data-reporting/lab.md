# Lab 03 — Structured Data & Reporting

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

`data/alerts.json` contains 50 simulated security alert records from Meridian Financial's SIEM.
Each record has `rule_id`, `severity`, `source_ip`, `destination_ip`, `dst_port`, `timestamp`,
and `description` fields — but several records have missing fields or duplicate fingerprints.

## Scenario
Meridian's SIEM exported a JSON dump of the last hour's alerts. The team wants a morning briefing
that is: (a) deduplicated — same rule firing on same source/dest counts as one; (b) summarised
by severity; (c) available as a CSV for the ticket system; and (d) readable as a terminal table
for the analyst on call. Build `report.py` to do all four.

> Everything runs locally against bundled data. No authorization issues.

## Do
1. [ ] Read `data/alerts.json` with `json.load()`. Print the total record count and the count of
   unique `rule_id` values. (This is your sanity check before you process anything.)
2. [ ] Deduplicate: define a fingerprint as `(rule_id, source_ip, destination_ip, dst_port)`.
   Use a `set` to remove duplicates. How many records remain?
3. [ ] Filter: keep only records where `severity` is `"HIGH"` or `"CRITICAL"`. Use `.get()` for
   the severity field so missing-severity records are silently skipped.
4. [ ] Write the filtered, deduplicated alerts to `output/report.csv` using `csv.DictWriter`.
   Columns: `timestamp`, `severity`, `rule_id`, `source_ip`, `destination_ip`, `dst_port`,
   `description`.
5. [ ] Render a `rich` table to the terminal: one row per alert, severity colour-coded (CRITICAL
   = red, HIGH = yellow). Print a summary line below: total unique HIGH/CRITICAL alerts.
6. [ ] Handle the edge case: two records in `alerts.json` have a `null` severity field. Confirm
   your script handles them without raising a `TypeError`.

## Success criteria — you're done when
- [ ] `report.py` exits 0 and produces `output/report.csv`.
- [ ] The CSV has the correct headers and no duplicate rows.
- [ ] The terminal table colour-codes severity correctly.
- [ ] Null-severity records are skipped without crashing.
- [ ] The deduplication count matches what you calculated by hand for a 5-record sample.

## Deliverables
`report.py` + `output/report.csv`. Commit `report.py`; do not commit `output/` (add it to
`.gitignore`). The data file stays in `data/`.

## Automate & own it
**Required.** Add a `--severity` flag to `report.py` so the caller can set the minimum severity
threshold from the command line (e.g., `python report.py --severity MEDIUM`). Have a model draft
the `argparse` wiring; check that the argument validation fails gracefully on an invalid value
(e.g., `--severity BANANA`) and that the default behaviour is unchanged. Commit the updated script.

## AI acceleration
Ask a model to generate `report.py` from this lab description. Run it. Then deliberately feed it
the two null-severity records and the duplicate records — does it handle them? Where does it
crash or silently misbehave? Fix those cases yourself and document the fix in a comment. The
model's first draft is a time-saver; the version that handles real data is yours.

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
