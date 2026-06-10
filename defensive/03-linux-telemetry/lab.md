# Lab 03 — Make a Linux Host Talk

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/03-linux-telemetry
make up
```

This builds a Ubuntu 22.04 container with osquery 5.12.1 installed. A bundled
`data/audit.log` (realistic synthetic events including a privilege-escalation
sequence) and `data/audit.rules` are pre-loaded. Run `make demo` to see the
audit-log parser flag suspicious executions and osquery answer live host-state
questions from inside the container. Use `make shell` to drop into a shell and
run your own `osqueryi` queries.

## Scenario
Turn a Linux host into a sensor and capture the telemetry from a real (simulated) attacker action.

> Your own host/VM only.

## Do
1. [ ] Configure auditd to log process execution (`execve`) and access to one sensitive file path.
2. [ ] Run an Atomic Red Team Linux test (or a benign "attacker" action like adding a user) and find
   it in the audit log.
3. [ ] Use osquery to answer a live question — e.g. which processes currently have a network
   connection?
4. [ ] Note one detection you could build from what you captured.

## Success criteria — you're done when
- [ ] auditd captured a process-execution event you triggered.
- [ ] You answered a host question with an osquery SQL query.
- [ ] You can describe a detection from the telemetry.

## Deliverables
`linux-telemetry.md`: your audit rules, the captured event, your osquery query, and a detection idea.

## AI acceleration
Have a model draft the auditd rule and the osquery SQL — then verify the rule actually fires on your
test action and the query returns what you expect.

## Connects forward
Linux telemetry feeds the same detection (08) and hunting (11) modules; it's also the visibility
Track 05 (cloud) assumes.

## Marketable proof
> "I instrument a Linux host with auditd and osquery and capture real execution telemetry — the
> visibility cloud and detection work depends on."

## Automate & own it
**Required.** Package your audit rules + a set of osquery detection queries as a small deployable
config (AI drafts, you test each one fires); commit it.

## Stretch
- Compare what auditd, osquery, and an eBPF tool (e.g. Falco) each see for the same action.
