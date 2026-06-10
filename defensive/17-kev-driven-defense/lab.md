# Lab 17 — Exploit & Detect a Current KEV Entry

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/17-kev-driven-defense
make up        # build the analysis container (KEV refresh tool + detector)
make demo      # refresh KEV, surface the reference target, detect its exploit
make down
```

The analysis container ships `kev_refresh.py` (pulls the CISA KEV catalog and cross-references it
against a bundled map of [Vulhub](https://github.com/vulhub/vulhub) targets), `detect.py` (the
Log4Shell detection matcher), and bundled `data/` — a real snapshot of the current KEV catalog
(the most-recent entries plus every entry that has a runnable target) and a sample Solr access log
containing both benign traffic and a Log4Shell attack. `make demo` runs fully **offline** against
the snapshot; `make refresh` hits the **live** CISA feed so you work against today's list.

The exploit **target** is a Vulhub environment pulled on demand (`make target-up`) — it is not
committed, because it's a known-vulnerable image you stand up only inside the lab.

## Scenario
You run detection engineering for Meridian Financial. Every week new entries land on CISA's KEV
catalog — confirmed exploited in the wild. Your job: take a *current* KEV entry that you can actually
stand up, exploit it the way an attacker would, and ship the detection that catches it. You exploit it
precisely so you can prove your detection fires on the real attack traffic and stays quiet on the rest.

> Authorization: the Vulhub target you stand up is yours — attack it freely. The habit still matters
> everywhere else: only test systems you own or have explicit written permission to test (Vulhub,
> DVWA, PortSwigger Academy, targets you own).

## Do

1. [ ] Run `make refresh` to rank **today's** live CISA KEV catalog. Note the `catalogVersion` and how
   many recent entries have a runnable target vs. how many (Chrome, appliances) don't. Then
   `make recommend` for the single most-recent runnable entry — that's a candidate you could build out.

2. [ ] Run `make demo`. It surfaces the lab's **reference** target — Log4Shell (CVE-2021-44228:
   KEV-listed, ransomware-flagged) — and runs the detection over a captured access log. Read why 3 of
   9 requests match and 6 don't.

3. [ ] Stand up the real target: `make target-up` (clones Vulhub, starts Apache Solr 8.11.0 on `:8983`).
   Confirm the admin UI loads at `http://localhost:8983/solr/`.

4. [ ] Exploit it. Send the JNDI-lookup payload (the Vulhub README has the exact request) so the server
   attempts an outbound LDAP/RMI/DNS callback. You don't need a full RCE chain — triggering the lookup
   (e.g. a `dns://` callback you can observe) proves the vulnerability. Capture the request traffic.

5. [ ] Write the detection as a portable rule in `detection.yml` (Sigma-style: `logsource` + `detection`).
   It must match the JNDI signature **wherever it lands** — URI, header, *and* User-Agent — not just the
   URI. Run it against your captured traffic with `detect.py` (extend it if needed) and confirm it fires.

6. [ ] Prove **no false positives**: run your detection against a benign-only log (strip the attack lines
   from the sample, or capture clean Solr traffic) and confirm zero hits. A detection that flags benign
   admin calls is worse than none.

7. [ ] `make grade` to check your work (writes `receipt.json` on an all-pass).

## Success criteria — you're done when
- [ ] You can name the current `catalogVersion` and explain why a recent KEV entry (e.g. a Chrome CVE)
  has no Vulhub target while an older one (Log4Shell) does.
- [ ] You triggered the vulnerability on the live Vulhub target and captured the request.
- [ ] Your `detection.yml` fires on the attack traffic (URI **and** User-Agent variants) and produces
  zero hits on benign traffic.
- [ ] `kev-target.md` records the CVE, why you chose it, the exploit, and the detection logic.

## Deliverables
`kev-target.md` (the CVE you chose and why, the exploit, and your detection writeup) and `detection.yml`
(the portable rule). Reference the captured traffic — **never commit the capture, the cloned Vulhub
target, or `receipt.json`** (they're gitignored).

## AI acceleration
Paste the chosen CVE's advisory into a model and ask for the exploit signature and a draft Sigma rule —
a real time-saver. Then verify every claim against the CISA entry and vendor advisory, watch the rule
*actually fire* on your captured traffic, and confirm it's silent on benign requests. Models invent
CVE IDs, wrong version ranges, and over-broad rules; the draft is a lead, not the deliverable.

## Connects forward
The detection plugs straight into detection-as-code (module 08) and ATT&CK coverage (module 10:
Log4Shell maps to T1190, Exploit Public-Facing Application). The KEV-refresh tool becomes an enrichment
step in your SOAR playbook (module 16) — "is this CVE on KEV, and do we have coverage?" The exploit half
mirrors the offensive vuln-id triage (Track 01, module 03), seen from the defender's side.

## Marketable proof
> "I operationalise the CISA KEV catalog: I refresh against the live feed, stand up a current
> exploited-in-the-wild CVE in a contained lab, exploit it, and ship a detection that fires on the
> attack and stays quiet on benign traffic — closing the loop from threat intel to coverage."

## Automate & own it
**Required.** With AI drafting and you reviewing every line, turn the manual refresh into a standing
check: extend `kev_refresh.py` to **diff** today's live catalog against the bundled snapshot and print
only the *new* entries since, flagging which have a runnable target. That "what's new on KEV, and can we
cover it?" report is the reusable artifact — commit it alongside your detection.

## Stretch
- Map two more recent KEV entries (e.g. the Jenkins or Confluence targets the tool surfaces) to their
  Vulhub envs in `data/vulhub_catalog.json`, exploit one, and write its detection — proving the loop
  generalises beyond Log4Shell.
- Wire the diff report into a scheduled job (cron/GitHub Action) that opens an issue when a new KEV
  entry has a target you don't yet detect.
