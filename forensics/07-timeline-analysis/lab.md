# Lab 07 — Timeline Analysis

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/07-timeline-analysis
make up        # build the plaso container
make demo      # run log2timeline against the bundled artifacts, filter with psort, display
make shell     # drop in to explore interactively
make down      # stop when done
```

The container includes `log2timeline.py` (plaso) and `psort.py`. Seed data:
- `data/artifacts/` — mixed log files for plaso ingestion (EVTX-shaped JSON, web server log, browser history snippet, prefetch-shaped JSON)
- `data/timeline.csv` — pre-computed timeline from the full Meridian scenario for analysis exercises

> Everything runs locally against bundled data. No authorization needed.

## Scenario
The Meridian IR investigation has now collected artifacts from five sources: Windows Security events, the finance user's browser history, web server logs from the internal file share, a prefetch artifact, and a memory capture timestamp. Your task is to **build a super-timeline** from these sources and answer the question the IR lead is asking: *"Give me a 60-second walk-through of what happened, in order, with a timestamp for every key action."*

> In a real investigation, timeline inputs would be forensically acquired and hash-verified artifacts from earlier phases of the investigation.

## Do

1. [ ] **Run log2timeline against the artifact directory.**
   ```bash
   log2timeline.py /tmp/timeline.plaso data/artifacts/
   ```
   Watch the output: which parsers fired? Which files were successfully parsed? Note any parser errors — they often indicate a malformed or unexpected file format.

2. [ ] **Export and sort the timeline.**
   ```bash
   psort.py -o l2tcsv /tmp/timeline.plaso > /tmp/timeline-all.csv
   ```
   How many events were produced? Open the CSV and examine the columns: `datetime`, `timestamp_desc`, `source`, `source_long`, `message`, `display_name`.

3. [ ] **Filter to the incident window.**
   Use `psort.py` filters to narrow to the incident window (2024-03-15 02:00:00 to 02:35:00 UTC):
   ```bash
   psort.py -o l2tcsv \
     --slice "2024-03-15T02:00:00" --slice_size 35 \
     /tmp/timeline.plaso > /tmp/timeline-incident.csv
   ```
   How many events fall in the window? Print and review them in chronological order.

4. [ ] **Analyze the pre-computed Meridian timeline.**
   Open `data/timeline.csv` — a richer pre-computed timeline from the full scenario. Find and note (with timestamps) the following events:
   - The first indication of attacker access (failed logon attempt)
   - The successful logon from the attacker's IP
   - The first browser search indicating intent
   - The file download event
   - The process creation chain (cmd.exe → powershell.exe)
   - The file access events on the restricted share
   - The log clear event
   - The last attacker event before the IR team arrived

5. [ ] **Identify gaps and anomalies.**
   Look for:
   - Any gap of more than 5 minutes in the incident window — what does the absence of events suggest?
   - Any event whose timestamp is inconsistent with the sequence (e.g., a file "created" before the attacker logged in — possible timestomping).
   - Any event source that contradicts another (e.g., browser says download happened at 02:09, but filesystem says file appeared at 02:12 — 3-minute gap: explanation?).

6. [ ] **Write the IR timeline narrative.**
   Produce `timeline-narrative.md` with:
   - A table: timestamp (UTC) | source | event description | significance
   - A 200-word prose narrative: "At 02:09 UTC, the attacker…" — every sentence cites a specific timestamp and source.
   - A "gaps and anomalies" section noting anything that needs further investigation.

## Success criteria — you're done when
- [ ] `log2timeline.py` ran and produced a plaso store without critical errors.
- [ ] `psort.py` produced a filtered incident-window CSV.
- [ ] At least 8 key events from the Meridian scenario are documented with timestamps in `timeline-narrative.md`.
- [ ] At least one gap or anomaly is identified and its investigative significance explained.
- [ ] The prose narrative traces every claim to a specific event source and timestamp.

## Deliverables
Commit `timeline-narrative.md` to your fork. This is the primary deliverable — it's the kind of document that goes in front of an IR lead or legal team. Do not commit `/tmp/timeline.plaso` or `/tmp/timeline-all.csv`.

## Automate & own it
**Required.** Write a Python script `timeline-pivot.py` that:
1. Reads a CSV timeline file (output from `psort.py`).
2. Accepts a time window (start, end) and an optional keyword filter.
3. Outputs a Markdown table of matching events, sorted by timestamp.
4. Flags events from multiple sources within 60 seconds of each other ("corroborated events").

Have a model draft the script; **read every line** and run it against `data/timeline.csv` before committing. This is the automation move for timeline pivoting: a scriptable filter you can run during an active investigation without needing Timesketch standing up.

## AI acceleration
Take a 20-event window from `data/timeline.csv` and feed it to a model. Ask: "Given these events in order, what is the attacker's technique at each step, and what ATT&CK technique ID corresponds?" Then verify every technique ID at [attack.mitre.org](https://attack.mitre.org). Use the model to draft the prose narrative from your annotated table — then trace every sentence back to the specific CSV row before finalizing.

## Connects forward
The super-timeline is the spine of the track's capstone — all subsequent modules (network forensics, triage, reporting) feed artifacts back into the timeline. The narrative you write here is the draft of the incident report you'll finalize in Module 14.

## Marketable proof
> "I build and pivot forensic super-timelines with plaso — correlating events from event logs, browser history, filesystem, and memory across a multi-hour incident window into a narrative that traces every claim to an artifact."

## Stretch
- Set up Timesketch locally (Docker deployment) and import your plaso store. Use the search interface to find all events involving the IP `10.99.4.22` across all sources. How does this compare to grep-based search on the CSV?
- Research how plaso handles timezone normalization: what happens if an artifact is in local time instead of UTC? How does `psort.py` report this?
