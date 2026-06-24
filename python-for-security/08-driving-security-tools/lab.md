# Lab 08 — Driving Security Tools

*Hands-on lab · [← Back to the module concept](README.md)*

> **Lab environment: real-feed rewire — validation deferred.** The VT-shaped enrichment API now
> serves real abuse.ch data (Feodo Tracker + URLhaus) from `feeds/db.json` instead of synthetic
> detection ratios; the IOC list is real abuse.ch IOCs. (MISP stays local — it is the
> system-of-record the analyst writes to.) `make up && make demo && make down` has **not** yet been
> re-run on a clean Linux runner against this change; validate before marking the lab done.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/08-driving-security-tools
make up        # starts local MISP + real-feed VT-shaped API + student container
make demo      # runs the full workflow: create event → enrich → tag
make refresh   # (optional, needs network) re-fetch the LIVE abuse.ch feeds into feeds/db.json
make shell
make down
```

Three containers: a **local MISP** instance (real MISP API shape) on port 8080; a **VirusTotal-shaped
enrichment API** on port 8081 backed by **real abuse.ch threat intel** (Feodo Tracker + URLhaus,
served from `feeds/db.json` with `source`/`fetched_at` provenance); and the **student container**
with `pymisp` and `httpx` installed.

`data/iocs.txt` contains 10 real IOCs — malicious botnet C2 IPs from Feodo Tracker, URLhaus
malware-sample ids, and two known-clean public resolvers. The VT-shaped API returns a real
detection verdict for each (high malicious-engine count for the real C2 IPs, zero for the clean
resolvers). Run `make refresh` to pull today's live IOCs.

> **Authorization note:** These tools run against a local MISP and a local copy of real feed data.
> In production, MISP and VT API calls affect real shared threat intelligence — always review
> before publishing events to a community instance.

## Scenario
Your CSIRT received a phishing report. The analyst extracted 10 IOCs from the email headers and
attachments — here, real abuse.ch-sourced IOCs. Your task: create a MISP event for the incident,
add all 10 IOCs as attributes with correct types, enrich each with the (real) VT-shaped detection
ratio, tag the event with TLP:AMBER, and mark it ready for review.

## Do
1. [ ] Browse the mock MISP UI at `http://localhost:8080` and skim the `pymisp` quickstart so you
   know the object model (event → attributes → tags) before you script it. (Run `make demo` only at
   the end — it builds the reference event, which you'll diff your own against.)
2. [ ] Write `workflow.py` using `pymisp`:
   - Connect to `http://misp:8080` with the API key from `os.environ["MISP_KEY"]` (pre-set
     in the container).
   - Create a `MISPEvent` with `info="Phishing campaign — abuse.ch-sourced IOCs"`, threat level 2,
     analysis 1.
   - For each IOC in `data/iocs.txt`, detect the type (`ip-dst` for IPs, `other` for the numeric
     URLhaus sample ids) and add it as an attribute.
3. [ ] Enrich each attribute: query the VT-shaped API at `http://vt-api:8081/api/v3/ip_addresses/<ip>`
   or `.../files/<sample_id>` and attach the (real) detection ratio as the attribute's `comment`
   field.
4. [ ] Tag the event: `tlp:amber` and `misp-galaxy:mitre-attack-pattern="Phishing T1566"`.
5. [ ] Publish the event and print its MISP URL.
6. [ ] Verify: query MISP for events with tag `tlp:amber` and confirm your event appears.
7. [ ] Run `make demo` and compare the reference event against yours — same attribute types, same
   tags, same enrichment comments? Where they differ, decide which is correct and why.

## Success criteria — you're done when
- [ ] The MISP event exists in the mock instance with all 10 attributes.
- [ ] Each attribute has a non-empty `comment` with the VT detection ratio.
- [ ] The event carries both `tlp:amber` and the ATT&CK tag.
- [ ] The event query by tag returns your event.

## Deliverables
`workflow.py`. Commit it. Do not commit any API keys (they come from environment variables).

## Automate & own it
**Required.** Refactor `workflow.py` into a function `process_incident(iocs: list[str],
title: str) -> str` that returns the MISP event URL. Write a `test_workflow.py` that mocks
the MISP and VT API calls using `unittest.mock.patch` and tests that the function creates the
correct event structure without making real HTTP calls. Have a model draft the mocks; review
that the patched calls actually prevent network access (test it by turning off the mock containers
and running the tests — they should still pass). Commit `test_workflow.py`.

## AI acceleration
Ask a model to write the `pymisp` attribute-adding loop with type detection. Then check: does
it correctly distinguish `sha256` (64 chars) from `md5` (32 chars)? What does it do with a
domain? What about a URL? Test each case explicitly — threat intel with the wrong attribute type
is misleading, not useful.

## Connects forward
The MISP integration becomes the "create ticket" action in the SOAR playbook in Track 10 module
08. The enrichment pattern is the same one used throughout this track and the automation track.

## Marketable proof
> "I automate threat-intel workflows with pymisp — create events, add typed attributes, attach
> enrichment, tag with TLP — so the CSIRT gets a pre-enriched event instead of a list of IOCs
> to look up by hand."

## Stretch
- Use the `pymisp` object model (`MISPObject`) to attach a `vt-report` object to each attribute
  rather than a comment string — this is the correct structured way to attach enrichment in MISP.
- Add a `--dry-run` flag that prints what would be created without making any API calls.
