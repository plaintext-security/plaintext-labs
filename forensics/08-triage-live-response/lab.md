# Lab 08 — Triage & Live Response with Velociraptor

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/08-triage-live-response
make up      # starts Velociraptor server + enrolled endpoint agent
make demo    # runs a VQL artifact collection and prints structured results
make shell   # drops into the agent container to explore
make down    # stop everything when done
```

The environment runs two containers: a Velociraptor server (with the admin GUI available
at `http://localhost:8889`) and a single enrolled Linux endpoint agent. `make demo` connects
the agent, executes three VQL artifacts (process list, network connections, recently modified
files), and prints the results to stdout without any GUI interaction required.

> All data is synthetic and local. No external targets are involved.

## Scenario

Meridian Financial's SIEM fired a high-severity alert: a PowerShell-like interpreter process
spawned under the developer account `mfin\dev-svc01` on `WORKSTATION-04`. Your task is to
determine whether the activity is isolated to that one host or whether the attacker has moved
laterally to other systems. You have thirty minutes before the on-call manager needs a scope
estimate.

The lab simulates Meridian's environment as a single enrolled endpoint. Run the same triage
workflow a real responder would execute against the full fleet.

> Only examine evidence you are authorised to handle. In a real engagement, Velociraptor
> hunts require organisational approval before deployment to production endpoints.

## Do

1. [ ] **Run `make demo`** and read all three artifact outputs. Which process in the process list
   is anomalous — what parent/child relationship or image path stands out? Note the PID and
   the name.

2. [ ] **Investigate the network connection table.** Does the anomalous process have an active
   or recent outbound connection? What IP and port? Is that port consistent with the protocol
   the binary name implies, or does it look like port mimicry? (Hint: look at the combination
   of `RemoteAddr` and `State` columns.)

3. [ ] **Write a custom VQL query** to find every file modified in the last two hours under
   `/tmp` and `/var/tmp`. (Build it from the `glob()` plugin with a recursive glob, select the
   path/mtime/size columns, and add a `WHERE` on the modification time — note Velociraptor times
   are in microseconds, so work out the two-hour cutoff in those units.) Run it via `make shell`
   inside the agent container using the `velociraptor ... query` subcommand against the client
   config. Did anything show up that wasn't there before the demo seeded the environment?

4. [ ] **Scope decision.** Based on process, network, and file evidence, is this host "in scope
   for full imaging" or "low confidence, monitor"? Write a one-paragraph triage note that a
   non-technical manager could read, citing each artifact finding.

5. [ ] **Explore the GUI** (optional but recommended): open `http://localhost:8889` in your
   browser (credentials in `make up` output) and find the enrolled client. Browse the
   "Collected Artifacts" for the demo run — see how the server stores results for later analysis.

## Success criteria — you're done when

- [ ] You have identified the anomalous process by name and PID from the artifact output.
- [ ] You have documented whether the process has an active outbound connection and to what.
- [ ] Your custom VQL query ran and returned results (even if the result set is empty — empty is a
  valid finding).
- [ ] You have written a one-paragraph triage note with artifact citations.

## Deliverables

Commit to your portfolio repo:
- `triage-note.md` — your scoping assessment with process, network, and file findings cited by artifact name and field values.
- `custom.vql` — the VQL query you wrote in step 3 (or a refined version).

Lab-generated output (logs, result JSONs) is **not committed** — reference the artifact names in your note instead.

## Automate & own it

**Required.** Write a Python script `triage_report.py` that:
1. Accepts a Velociraptor artifact result as a JSON file (use the demo output files in `data/`).
2. Parses the process list and flags any process whose `CommandLine` contains an encoded string
   (base64 blob), a double-extension (`invoice.pdf.exe`), or a path outside expected system directories.
3. Prints a brief "suspicious items" report to stdout.

Use a model to draft the script; **read every line of output logic** before running it against real
data. A triage script that silently misses encoded commands is worse than no script — it gives false
confidence. Commit `triage_report.py` alongside your deliverables.

## AI acceleration

Paste the process list JSON into a chat session and ask the model to rank suspicious entries and
explain why. Compare its top picks against what you identified manually — where do they agree?
Where does human context (knowing what software is expected on a developer workstation) cause you
to override the model? Document one disagreement and your reasoning. That disagreement is the
skill the job pays for.

## Connects forward

Module 09 (Network Forensics) picks up the network connection you identified here and reconstructs
the session from a PCAP. Module 13 (IR Process) uses the triage note format as the input to the
NIST containment decision.

## Marketable proof

> "I deploy Velociraptor live-response collections across endpoint fleets, write VQL artifact
> queries, and produce scoped triage notes that distinguish in-scope hosts from noise in minutes —
> not days."

## Stretch

- Write a VQL artifact that checks all running processes against VirusTotal's API (using
  `http_client()` in VQL) and flags any with a positive ratio above 0. Run it in the GUI and
  see the enriched results.
- Add a second service to the `docker-compose.yml` — a second endpoint agent — and run the demo
  hunt against both. Observe how the server correlates results across clients.
