# Module 17 — KEV-Driven Defense

*Type 5 · Detonate & Detect — refresh against the live CISA KEV catalog, select a current entry with a reproducible target, exploit it in a contained lab, and write a detection that fires on the attack while staying quiet on benign traffic; you commit the exploit-and-detect pair. (Secondary: Drift/Steady-State — diff the feed, because a catalog you finished last month is already behind.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Defensive Operations** — *defend against what's actually being exploited this week, not the CVE wall.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
A defender drowning in CVEs is a defender who patches the wrong thing. CISA's Known Exploited
Vulnerabilities (KEV) catalog is the single best free signal for "this is being used against real
organisations *right now*" — and it changes every few days. The job is to make that feed *operational*:
turn "what's current" into a target you can stand up, attack, and then **detect** — so your monitoring
covers the threat before it reaches you, not six months after. This closes the offense↔defense loop
from the inside: you exploit a real KEV entry, then write the detection that would have caught you.

## Objective
Refresh against the live CISA KEV catalog, select a current entry with a reproducible target,
exploit it in a contained lab, and write a detection that fires on the attack while staying quiet on
benign traffic.

## The core idea
Module 03 (offensive vuln-id) taught the triage call: KEV beats raw CVSS because "confirmed exploited
in the wild" outranks "theoretically severe." This module takes the *defensive* consequence of that
call and makes it a loop. KEV is not a static list you read once — it is a feed with a `catalogVersion`
and a `dateAdded` on every entry, and CISA adds to it continuously. So the first skill is mechanical
and underrated: **pull the current catalog, diff it against last time, and know what's new.** A
detection programme that was "complete" last month is already behind if three KEV entries landed since.

The bridge most learners miss is between *"it's on the KEV list"* and *"I have a target I can actually
work."* Not every KEV entry is reproducible — a Chrome V8 bug or a Cisco appliance RCE has no friendly
container — but a large fraction map to a [Vulhub](https://github.com/vulhub/vulhub) environment
(a per-CVE `docker-compose` for known-vulnerable software). The practitioner move is to cross-reference
the live feed against "what can I stand up," pick the most recent *runnable* entry, and exploit it. That
is exactly what a detection engineer does when validating coverage: you can't trust a detection you've
never seen fire.

Then comes the half that pays the rent: **detection.** Exploiting the bug proves it's real; shipping
the detection is the deliverable. The discipline is to write the rule against *the same traffic your
exploit produced*, then prove it stays silent on benign requests. Log4Shell (CVE-2021-44228, KEV-listed,
ransomware-flagged) is the cleanest teaching case: the `${jndi:ldap://…}` lookup string lands in the URI,
a header, or the User-Agent, and a detector that only checks the URI misses the User-Agent variant — a
concrete lesson in why field coverage matters. The judgment to carry: KEV tells you it's exploited and
Vulhub tells you it's reproducible, but both are *leads* — you still read the advisory and the PoC before
you run anything, and a model that "summarises today's KEV adds" will cheerfully invent a CVE ID or a
wrong `dateAdded`. Verify against CISA every time.

## Learn (~3 hrs)

**The KEV catalog as an operational feed**
- [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) — the catalog page: what gets added, the `dueDate` model, and the link to the JSON feed you'll automate against. Read the "Criteria" box.
- [cisagov/kev-data (CISA's own GitHub mirror)](https://github.com/cisagov/kev-data) — CISA publishes the catalog here as CSV/JSON with full git history, synced within minutes of the canonical source. This is the feed your tool pulls (and its documented fallback when `cisa.gov` blocks non-browser clients); the commit log *is* the "what's new since last time" diff.

**Reproducible targets**
- [Vulhub](https://github.com/vulhub/vulhub) — pre-built per-CVE `docker-compose` environments; skim the top-level README, then open [`log4j/CVE-2021-44228`](https://github.com/vulhub/vulhub/tree/master/log4j/CVE-2021-44228) to see how one entry is laid out (compose file + a README with the working exploit).

**The reference case — Log4Shell**
- [NCSC-NL/log4shell](https://github.com/NCSC-NL/log4shell) — the Dutch NCSC's curated operational reference for CVE-2021-44228: the `detection & mitigation/` folder gives you the JNDI-lookup signature and regex patterns, and `software/` shows the blast radius. Far more useful than a blog because it's the defender's playbook, sourced and maintained.
- [Vulhub's CVE-2021-44228 README](https://github.com/vulhub/vulhub/blob/master/log4j/CVE-2021-44228/README.md) — the exploit you'll run, step by step: the `${jndi:ldap://…}` payload against Apache Solr's admin endpoint. ~10 min; it makes the detection signature concrete.

## Key concepts
- KEV is a *moving feed* (`catalogVersion`, `dateAdded`) — refreshing and diffing is the skill
- KEV > CVSS for prioritisation, applied to *defensive coverage* not just attacker triage
- Cross-referencing "exploited in the wild" against "reproducible target" (Vulhub)
- Exploit → detect loop: write the rule against the traffic your own exploit produced
- Field coverage in a detection (URI vs header vs User-Agent) and proving no false positives
- Leads, not gospel: verify the CVE, advisory, and PoC against CISA before acting

## AI acceleration
A model is genuinely useful for turning a fresh KEV entry into a starting detection — paste the advisory
and ask for the exploit signature and a draft Sigma rule. But it hallucinates here readily: a wrong
affected-version range, an invented CVE ID, or a `dateAdded` that doesn't match the catalog. Treat the
draft as a lead: verify every claim against the CISA entry and the vendor advisory, watch the rule
actually fire on your captured exploit traffic, and confirm it stays quiet on benign requests. AI drafts
the rule; you make it fire, you map it, you own the alert.
