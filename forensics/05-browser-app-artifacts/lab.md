# Lab 05 — Browser & Application Artifacts

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/05-browser-app-artifacts
make up        # build the hindsight + sqlite3 container
make demo      # extract and display browser artifacts from the seed History file
make shell     # drop in to work interactively
make down      # stop when done
```

The container includes `hindsight` and `sqlite3`. `data/History` is a small SQLite Chrome
history database — modelled on the public **Nitroba University Harassment** scenario (Digital
Corpora). For the *real* artifact, `make fetch-data` pulls the Nitroba PCAP
(`https://downloads.digitalcorpora.org/corpora/scenarios/2008-nitroba/nitroba.pcap`, ~60MB), from
which the suspect's webmail sessions and browser/user-agent artifacts can be reconstructed.

> Everything runs against a bundled SQLite file you own. No authorization needed.

## Scenario
This lab is built on the public **Nitroba University Harassment** case (Digital Corpora): chemistry
instructor *Lily Tuckrige* receives a string of harassing emails, and investigators sniff dorm
network traffic to identify which student sent them — reconstructing the suspect's **webmail
activity and browser artifacts** from the capture.

Here you work the browser-artifact angle: the analyst imaged the suspect's Chrome profile and
extracted the `History` file (`data/History`). The account of interest (`jsmith`) claims they only
used the browser for "normal coursework." Your task is to **reconstruct the browser/webmail
activity** during the harassment window and determine whether the evidence supports or contradicts
that claim. To work the *real* network artifact, run `make fetch-data` and carve the webmail
sessions out of `nitroba.pcap`.

> Only examine browser artifacts from systems you are authorised to investigate. The Nitroba PCAP
> is published for training; in a real case these files arrive via a forensically acquired image or
> a lawful capture.

## Do

1. [ ] **Run hindsight against the History file.**
   ```bash
   hindsight.py -i data/ -o /tmp/hindsight-output -f xlsx
   ```
   Open the XLSX (or run with `-f jsonl` and `cat` the output). What does hindsight report for:
   - Total URLs visited
   - Date range of the history
   - Top visited domains

2. [ ] **Query visited URLs directly with sqlite3.**
   Write your own query over the `urls` table (fields: `url`, `title`, `visit_count`,
   `last_visit_time`) ordered by most-recent visit. Chrome stores timestamps as microseconds
   since 1601-01-01, not the Unix epoch — convert them to readable UTC in your `SELECT` so the
   times line up with the incident window (2024-03-15 02:00–02:35 UTC). Which URLs fall in that
   window? Note any webmail, anonymous-mailer, or anonymizer domains.

3. [ ] **Examine the downloads table.**
   Query the `downloads` table (fields like `target_path`, `tab_url`, `total_bytes`, `state`,
   `start_time`) the same way, converting `start_time`. What was downloaded, and from where?
   Does the download URL align with the harassment narrative (an anonymous-mailer tool)?

4. [ ] **Extract search terms.**
   Search terms live in `keyword_search_terms` (`term`, `url_id`), which you join to `urls` on
   `urls.id` to recover the URL and timestamp. Write that join. What search terms appear — do any
   suggest the user was looking for ways to send untraceable email or hide their IP address?

5. [ ] **Check the WAL file.**
   The `data/History-wal` (if present) may hold rows written after a history clear that the main
   database file doesn't yet show. Count the `urls` rows, force a WAL checkpoint, then count
   again. (Which `PRAGMA` flushes the WAL into the main database?) Does the row count change? This
   demonstrates why clearing browser history doesn't necessarily wipe the WAL.

6. [ ] **Write your findings.**
   Produce `browser-findings.md` with:
   - Timeline of browser activity during the incident window (2024-03-15 02:00–02:35)
   - Downloads found and their source URLs
   - Search terms that are relevant to the investigation
   - Assessment: does the browser history support or contradict the user's claim of "normal coursework"?
   - Short paragraph on what private/incognito mode would and wouldn't have hidden in this scenario.

## Success criteria — you're done when
- [ ] hindsight has been run and its output reviewed.
- [ ] At least 5 URLs from the incident window are documented with timestamps.
- [ ] Downloads table was queried and findings documented.
- [ ] Search terms were extracted and assessed for relevance.
- [ ] `browser-findings.md` includes a clear assessment of the user's claim.

## Deliverables
Commit `browser-findings.md` to your fork. Do not commit `/tmp/hindsight-output/` or any modified copies of the `History` file.

## Automate & own it
**Required.** Write a Python script `browser-triage.py` that:
1. Takes a path to a Chrome `History` SQLite file and a time window (start, end) as arguments.
2. Queries and outputs: URLs visited in the window, downloads, and search terms.
3. Formats the output as a Markdown table.
4. Flags any URLs matching a list of known anonymous-mailer / anonymizer or file-sharing domains (e.g., `willselfdestruct.com`, `sendanonymousemail.net`, `mega.nz`, `wetransfer.com`).

Have a model draft the script; **read every line** including the timestamp conversion — that's the most error-prone part. Test it against `data/History` and verify at least one timestamp against the hindsight output before committing.

## AI acceleration
Feed the browser history output to a model and ask it to identify which domains are anonymous-mailer / anonymizer services relevant to a harassment investigation. Ask it to explain the Chrome timestamp epoch conversion and generate a SQL query for a specific time window. Verify every timestamp it produces by checking a known reference visit against the SQL output — the epoch conversion is the most common source of error.

## Connects forward
Browser artifacts feed the super-timeline in Module 07 (plaso parses Chrome history natively and merges it with EVTX and filesystem events). The download records connect to Module 06 (if a malicious payload was downloaded, the memory forensics module will show it running).

## Marketable proof
> "I extract and correlate browser artifacts — history, downloads, search terms, and WAL data — using hindsight and direct SQLite queries, and I can tell you whether a user's claimed activity matches what the browser actually recorded."

## Stretch
- Research how Firefox stores its history (it's also SQLite, but the schema differs). Write a Python snippet to query `places.sqlite` for the same fields you extracted from Chrome.
- Look up what incognito mode *does* preserve: DNS cache (OS-level), network flow data, proxy logs. Sketch a scenario where you could partially reconstruct incognito browsing from non-browser sources.
