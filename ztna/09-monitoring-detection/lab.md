# Lab 09 — Detection in a Zero Trust Environment

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/09-monitoring-detection
make up        # build + start the container (sigma-cli + the offline matcher)
make demo      # see the worked example: unexpected-country rule fires against ZT access logs
make shell     # drop into the container to work
make down      # stop it when you're done
```

The container bundles `sigma-cli` and the same offline teaching matcher used in the defensive track (adapted for ZT access log structure). Sample ZT access telemetry lives in `data/access-logs.jsonl` — 20 real-shaped structured events from the fictional **Meridian Financial** ZT environment, with several anomalies planted. The worked example rule is in `examples/`.

> Everything runs locally against bundled data you own. No external targets, no authorization needed.

## Scenario

Meridian Financial has completed their Pomerium pilot (module 06) and every internal service now logs access events to a central SIEM. The logs are structured JSONL — each event carries user identity, device, country, service, action, and data volume. The security team wants two detection rules operational before the production rollout:

1. **Unexpected country login** — a valid session authenticated from outside Meridian's operating countries (US, CA, GB, DE, AU). This is the leading indicator for credential compromise.
2. **Auth failure flood** — six or more `auth_failed` events for the same user within a few minutes. Classic credential-stuffing or token-replay attempt.

The seed data contains both signals. Your job: write and validate the rules, reason about false positives, and automate the detection as code.

## Do

1. [ ] **Read the seed data.** Open `data/access-logs.jsonl` and note the field structure: `event_type`, `user`, `country`, `device_posture`, `bytes_sent`. Find the events that look anomalous without running any rules — the auth flood, the unexpected country, and the unusual data-volume pattern should be visible by eye.

2. [ ] `make demo` and read the output. The example rule (`examples/zt-unexpected-country.yml`) fires on the unexpected-country event. Which log line? What is the user and country? Note: this is a `selection and not filter` rule — understand which field the `filter` is excluding.

3. [ ] **Understand the filter.** Open `examples/zt-unexpected-country.yml`. The `filter` stanza lists the expected countries. What would happen if you removed the filter entirely? How many events would fire? Verify your answer by temporarily removing the filter stanza and running `make detect RULE=examples/zt-unexpected-country.yml`.

4. [ ] **Write a second rule: auth failure flood.** Create `auth-flood.yml`. A detection rule for six or more `auth_failed` events for the same user is beyond this offline matcher's condition grammar (it requires aggregation). Instead, write a simpler rule that fires on any single `auth_failed` event from a source_ip that is not in the RFC 1918 private ranges (i.e. a non-internal IP). Hint: use `event_type: auth_failed` in selection and a filter that matches `source_ip|startswith` on private prefixes (`10.`, `172.`, `192.168.`, `127.`).
   ```bash
   make detect RULE=auth-flood.yml
   ```
   How many events does it fire on? Do they correspond to the flood you saw by eye?

5. [ ] **Write a third rule: data volume anomaly.** A single `access_allowed` event with `bytes_sent` above 100000 (100KB) on the `hr-portal` service may indicate a bulk export. Use `bytes_sent|gte` (note: the offline matcher does not support `gte` — you'll need to add a numeric comparison to `detect.py`, or use a `|contains` trick with the string representation). Document whether the offline matcher supports this pattern and what the production SIEM query would look like instead.

6. [ ] **Reason about what ZT changes for detection.** Write a short note in your deliverable addressing:
   - Why is `auth_failed` higher fidelity in ZT than at a perimeter firewall?
   - What would an attacker who has a valid token (credential compromise, not brute force) look like in these logs? Which field would be your best signal?
   - What does "trust nothing" mean for detection coverage: more signal, less signal, or different signal?

## Success criteria — you're done when

- [ ] `make demo` fires on the unexpected-country event cleanly and exits 0.
- [ ] Your `auth-flood.yml` fires on all six auth-failure events in the flood and only those events.
- [ ] You've articulated whether the data-volume rule is implementable in the offline matcher and why.
- [ ] Your notes answer the three ZT-changes-detection questions in step 6.

## Deliverables

- `auth-flood.yml` — your Sigma rule for auth failures from external IPs
- `detection.md` — your notes: the anomalies you found by eye, the rule field logic, the ZT-changes-detection analysis

Commit both alongside the worked example rule. Lab artifacts stay out of commits.

## Automate & own it

**Required.** Add a `make verify` target that runs `detect.py` with `examples/zt-unexpected-country.yml` against the bundled logs and asserts it exits 0 (at least one hit). Then run `detect.py` with `auth-flood.yml` and assert it exits 0. This is the minimal regression test: if someone edits the seed data or the rule and breaks a detection, `make verify` catches it. Have a model draft the shell script; **you read every line** and confirm the exit-code assertions are correct.

## AI acceleration

Give a model the field structure from one log line and ask it to write a Sigma rule for "successful access from a country not in [US, CA, GB, DE, AU]." It will produce a working `selection and not filter` pattern quickly. Then test the deny side: add a clean US log event to a temp file and confirm the rule does NOT fire on it. AI rules frequently nail the hit case and miss filter edge cases — the filter list is the thing to verify manually.

## Connects forward

The ZT access log structure this module detects against is the output of what you built in module 06 (Pomerium logs) and what would be generated by the Cilium flow logs from module 07. A production Meridian deployment would feed all three log sources to the same SIEM and write Sigma rules across them — a single unauthorized access attempt from a non-compliant device would produce correlated signals in the ZT proxy log, the Cilium drop log, and the IdP audit log simultaneously. That correlation is the ZT detection advantage.

## Marketable proof

> "I can write Sigma rules against Zero Trust access logs, identify behavioral anomalies in structured identity-aware telemetry, and articulate why ZT logging changes the detection strategy compared to perimeter-era firewall logs."

## Stretch

- Write a Sigma rule for the data-volume anomaly (bulk export pattern on `hr-portal`) by extending `detect.py` to support a `|gte` numeric modifier. Commit the extended matcher alongside your rule.
- Write a correlation note: trace what events an attacker with a compromised credential (valid token, unexpected country) would generate across all three log sources from this track (Pomerium proxy log, Cilium flow log, OPA decision log). Map each event to an ATT&CK technique.
- Convert `zt-unexpected-country.yml` to an Elastic EQL query manually (not via sigma-cli) and confirm the field mapping against Cloudflare's published Access log field names.
