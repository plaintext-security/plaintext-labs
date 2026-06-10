# Module 05 — Browser & Application Artifacts

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *the browser is the most detailed diary of what a user actually did — and most people forget it exists.*

## Why this matters
Web browsers and desktop applications are the primary interface for most modern work — and most modern threats. A user who was phishing-targeted clicked something in a browser. An insider who exfiltrated data probably navigated to a cloud storage service or a webmail provider. A compromised machine is often first accessed via a malicious payload downloaded by a browser. Understanding what the browser recorded — and that it recorded far more than the visible history — is essential for reconstructing user activity during an incident.

## Objective
Extract browsing history, search terms, download records, and cached credentials from a Chrome/Chromium SQLite history database using `hindsight` and direct SQL queries; explain which browser artifacts survive private/incognito mode and which don't.

## The core idea
Every major browser stores its state in a collection of SQLite databases and JSON files on the local filesystem. Chrome and its derivatives (Edge, Brave, Arc) store history in `~/.config/google-chrome/Default/History` on Linux, `%LOCALAPPDATA%\Google\Chrome\User Data\Default\History` on Windows. This SQLite file contains tables for `urls` (every URL visited, visit count, last visit time), `visits` (each individual visit with transition type and referrer chain), `downloads` (filename, URL, byte count, state), and `keyword_search_terms` (search queries typed in the address bar). This is not a redacted log — it is a dense, timestamped audit trail of everything the browser navigated to, going back months or years unless manually cleared.

**What makes browser artifacts forensically rich** is that they are redundant. Clearing browser history removes the `urls` and `visits` table rows, but it does not clear the browser's DNS cache, the OS's DNS cache, the network flow data, or the download directory. More usefully for the forensic investigator: browser databases maintain a Write-Ahead Log (`History-wal`) and a journal file that often contain rows from before a clear was issued, because SQLite's WAL is not synchronously pruned when transactions commit. `hindsight` — a forensic tool purpose-built for Chrome-family browsers — understands this and reads both the main database and the WAL.

**Application-specific databases** follow the same pattern: Slack stores its workspace message history in a LevelDB database. Teams stores logs and media in `%APPDATA%\Microsoft\Teams`. Outlook stores email, contacts, and calendar in `.ost` (offline store) files — structured data formats that forensic tools can parse without a running application. The investigator's job is to know that "the user says they didn't download the file" is a testable claim, and that the SQLite download table, the `$MFT`, the prefetch, and the browser cache collectively either corroborate or contradict it.

**Hindsight** is a Python-based forensic tool from Google's internal DFIR team, released as open-source. It parses Chrome-family browser profile directories and produces structured output (XLSX, JSONL, HTML) of everything it finds: visited URLs sorted by timestamp, download records with source URLs, search terms, cookies, form autofill data, and extension state. For the forensic investigator, it provides a first-pass timeline of browser activity that can be fed directly into the super-timeline built in Module 07.

**Timestamps in browser databases** require care. Chrome's native timestamp format is the number of microseconds since January 1, 1601 UTC (Windows FILETIME epoch) — not the Unix epoch. Hindsight handles the conversion automatically; raw SQL queries require the manual conversion `datetime(visit_time / 1000000 - 11644473600, 'unixepoch')`. Getting the epoch wrong shifts all timestamps by 369 years in the wrong direction — a mistake that has produced confused forensic reports. Always verify a known timestamp (e.g., the last visit to a well-known site) against the expected value before trusting a conversion.

## Learn (~3 hrs)

**Browser forensics foundations (~1.5 hrs)**
- [hindsight — GitHub documentation](https://github.com/RyanDFIR/hindsight) — the tool's README and output field reference; read the Usage and Output sections before the lab.
- [Chrome SQLite Schema — Chromium source](https://source.chromium.org/chromium/chromium/src/+/main:components/history/core/browser/history_database.cc) — the authoritative schema; understand `urls`, `visits`, and `downloads` tables.

**SQLite forensics (~1 hr)**
- [SQLite WAL mode — official documentation](https://www.sqlite.org/wal.html) — explains why WAL files contain rows that history-clearing misses; short and essential for understanding forensic recovery.
- [DB Browser for SQLite](https://sqlitebrowser.org/) — the GUI tool for exploring SQLite files interactively; useful for understanding schema before scripting queries.

**Application artifacts (~0.5 hr)**
- [SANS Forensic Resources — Application Artifacts](https://digital-forensics.sans.org/blog/) — curated guides on where major applications (Slack, Teams, Office) store forensically relevant data; use as a reference during analysis.

## Key concepts
- Chrome stores history, downloads, and searches in SQLite databases in the user profile directory.
- Chrome's timestamp epoch is microseconds since 1601-01-01 UTC (not Unix epoch — conversion required).
- `hindsight` reads Chrome profile directories and outputs structured forensic reports including WAL data.
- WAL files often contain rows cleared from the main database — forensic gold.
- Browser artifacts are redundant: history, DNS cache, downloads, network flows each tell part of the story.
- Private/incognito mode does not write to the `urls`/`visits` tables — but DNS cache and network flows persist.
- Application artifact locations vary by OS; know where Slack, Teams, and Outlook store their data.

## AI acceleration
AI is useful for translating Chrome's timestamp format (feed it a raw microsecond value, get a human-readable datetime) and for drafting SQL queries against the browser schema. Where it's not reliable: it will guess at SQLite schema details and sometimes confuse the Chrome epoch with the Unix epoch. Always verify a timestamp conversion against a known event before trusting AI-generated SQL output.
