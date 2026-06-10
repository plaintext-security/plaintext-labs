# Module 09 — Monitoring & Detection in Zero Trust

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *"trust nothing" doesn't mean log nothing — it means log everything, with identity attached.*

## Why this matters

A common misconception about Zero Trust is that by eliminating trust you eliminate attack surface, making detection less important. The opposite is true: because every access request is authenticated and authorized at the proxy, every request is also logged — with full context: who, what device, from where, to which service, at what time, with what result. ZT moves you from "we log what crosses the perimeter" to "we have an audit trail for every lateral and north-south access." That is a detection windfall. But only if you write rules against it.

For a financial firm like Meridian, this matters both operationally and for compliance. NIST SP 800-207 and the CISA Zero Trust Maturity Model both call out continuous monitoring as a pillar — not an afterthought. The audit trail that proves every request was authorized is also the detection surface for when authorization is abused.

## Objective

Write a Sigma rule that detects a successful login from an unexpected country in a ZT access log, fire it against a bundled set of structured access events, and articulate how ZT-specific telemetry changes the detection strategy compared to perimeter-era logs.

## The core idea

In a traditional perimeter model, a SOC analyst sees firewall allow/deny logs and maybe some RADIUS authentication records — usually with no context about the user's device, their session history, or what they actually did after authenticating. An attacker who gets past the perimeter authentication is largely invisible in the east-west logs. Anomaly detection in this model is hard because baseline is sparse and unstructured.

ZT access logs invert this. Because every request requires a valid token and every token carries identity claims (user, email, IdP subject, groups, device posture score), the log record is already annotated with rich context at the access layer. The session-ID allows you to stitch a user's full access trace without joining across multiple log sources. The device ID and posture state are right there in each event — no separate MDM query. The `event_type` (access_allowed, access_denied, auth_failed) gives you the access decision in a machine-readable field, not buried in a message string. This structure makes writing precise detection rules much faster, and it makes correlating anomalies (multiple denials followed by a success, unusual bytes\_sent volume, unexpected country on a known device) tractable without heavy infrastructure.

The signal value of each event type is different. `auth_failed` events are noise in perimeter logs (bots constantly hammer login pages); in ZT they are higher fidelity because the IdP validates the token before it even reaches the proxy — an `auth_failed` event means something presented a token that failed validation, which is unusual. `access_denied` events are the proxy enforcing policy: a user with a valid token who hit a path their role doesn't cover — great signal for insider threat or compromised credential. `access_allowed` events are the full success path — and they carry the country, device, and data-volume fields that enable the behavioral rules (unexpected country, bulk export anomaly) that would never be detectable from perimeter logs alone.

One architectural note that practitioners often miss: because ZT proxies (Pomerium, Cloudflare Access, Zscaler) are the sole inbound path, there are no side channels to worry about. In a perimeter model, an attacker who bypasses the firewall produces no log. In ZT, bypassing the proxy means no connection — the service is not reachable. So the absence of a log is itself a control outcome, not a gap. Detection in ZT is not "did we see this go through the firewall?" but "did the proxy ever accept a request that policy should have denied?" — a tighter and more actionable question.

## Learn (~2.5 hrs)

**ZT and continuous monitoring (~45 min)**
- [Cloudflare Access audit logs documentation](https://developers.cloudflare.com/cloudflare-one/insights/logs/dashboard-logs/access-authentication-logs/) — a real-world ZT log structure reference; the field names in this lab's seed data mirror this structure. Read the "Access audit logs" section.

**Sigma and detection-as-code (~1 hr)**
- If you haven't done the defensive track: [Sigma rules — quick start (SigmaHQ GitHub)](https://github.com/SigmaHQ/sigma/wiki/) — the canonical rule-writing guide; covers `logsource`, `detection`, and the condition grammar needed for the lab's `selection and not filter` pattern.
- [Sigma rule collection — Cloud and ZT (SigmaHQ repo)](https://github.com/SigmaHQ/sigma/tree/master/rules/cloud) — real Sigma rules for cloud access events; useful reference for the field-naming conventions in this lab.

**Behavioral detection in identity-centric environments (~45 min)**

## Key concepts
- ZT proxies log every access decision — not just anomalies — with full identity and device context attached.
- `auth_failed` in ZT = invalid token presentation (unusual); in perimeter = bot noise (high volume, low signal).
- `access_denied` = valid identity, wrong policy — better insider threat and lateral movement signal than firewall drops.
- `access_allowed` events carry the fields needed for behavioral detection (country, device, bytes\_sent).
- Absence of a log in ZT = the proxy didn't allow it, not a gap. Detection question changes accordingly.
- Write Sigma rules with `selection and not filter` to detect unexpected-country access while excluding known-good countries.

## AI acceleration

AI can draft Sigma rules for ZT access log patterns quickly if you give it the log field names. Tell it the field structure from `data/access-logs.jsonl`, describe the pattern (e.g. "successful access from a country not in US, CA, GB"), and ask for a rule with `selection and not filter`. Then test it yourself: run `make detect` with a modified input that removes the anomalous event and confirm your rule produces zero hits (no false positives). Also confirm it fires on the actual anomalous event. AI rules pass the allow case and miss the filter edge cases more often than the other way around.
