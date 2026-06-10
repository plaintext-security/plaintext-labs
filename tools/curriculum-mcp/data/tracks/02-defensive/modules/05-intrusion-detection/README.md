# Module 05 — Intrusion Detection

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *signatures and anomalies on the wire — catching the known-bad as it happens.*

## Why this matters
NSM (module 04) gives you visibility; an IDS like Suricata gives you *alerts*. Suricata matches
traffic against rules — community rulesets like Emerging Threats encode thousands of real attacker
signatures — turning "here's all the traffic" into "here's the malicious bit." It's a SOC staple,
and you can test it against real malware traffic for free.

## Objective
Run Suricata with a community ruleset over real traffic, read the alerts it produces, and write a
simple rule of your own.

## The core idea
NSM (module 04) gives you a *record* — Zeek tells you what happened on the wire after the fact. An
IDS like **Suricata** gives you *opinions in real time*: "this specific traffic matches a known
exploit / this is a known C2 family — alert now." Two detection philosophies live in the one engine:
**signatures** (match known-bad byte patterns and behaviours — precise, but they only catch what
someone already wrote a rule for) and **protocol/anomaly logic** (catch malformed or policy-violating
traffic). Most of your value comes from community signatures — the Emerging Threats ruleset is
thousands of maintained rules encoding real attacker tradecraft — so, like SigmaHQ for the host, you
stand on others' work rather than writing from zero.

The distinction every network engineer already feels: an **IDS alerts; an IPS blocks.** Same engine,
different placement and risk appetite — put it inline to block and a false positive becomes an
outage, exactly the "detect vs. enforce" tension you live with on a firewall. Learning rule anatomy
(action, header, options, `sid`) pays off because reading a rule tells you what it actually keys on —
and whether it's brittle enough to evade with one changed byte.

The judgment: signatures are exact-match, which makes them simultaneously high-confidence and easy to
*evade* (new domain, new TLS, a padded payload) and easy to *over-trigger*. Tuning — fires on the
bad, stays quiet on the good — is the daily work, because a noisy ruleset trains analysts to ignore
alerts, which is worse than having no IDS at all.

## Learn (~4 hrs)

**The IDS**
- [Introduction to Suricata IDS (video)](https://www.youtube.com/watch?v=91i7InHVOso) — what Suricata is and how rule-based detection works.
- [Suricata documentation](https://docs.suricata.io/en/suricata-8.0.5/) — read "Quickstart" and the Rules intro; the authoritative reference.

**Rules**
- [Emerging Threats Open ruleset](https://rules.emergingthreats.net/) — the free community signatures Suricata ships against; the real-world detection content.

## Key concepts
- Signature (rule) vs anomaly detection
- Rule anatomy: action, header, options, `sid`
- Community rulesets (Emerging Threats) and how they're maintained
- IDS (alert) vs IPS (block)
- False positives and rule tuning

## AI acceleration
A model drafts and explains Suricata rules well — but a rule that's too broad floods the SOC and one
that's too narrow misses the variant. Test every generated rule against real traffic (fires on the
bad, stays quiet on the good) before trusting it.
