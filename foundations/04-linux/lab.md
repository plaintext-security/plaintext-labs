# Lab 04 — Investigating a Linux Host with Core Tools

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/04-linux
make up     # build + start the container (Ubuntu 22.04 with planted users + auth log)
make demo   # show expected triage output: users, SUID, processes, log analysis
make shell  # drop into the container to run the commands yourself
```

## Scenario
You've been handed shell access to a server and need to answer basic triage questions: who
can do what, what's running, and what do the logs say?

> Only run this against systems you own or this throwaway container.

## Do
Derive the commands yourself — the Learn resources and `man` pages are how. The goal, not
the keystrokes, is the point.

1. [ ] List every local account and work out which can become root. (Where do local users
   live? Which group grants `sudo`?)
2. [ ] Find every file that runs with its owner's privileges — the SUID set. (What
   permission bit is that, and how do you search the whole filesystem for it?)
3. [ ] Show the running processes, sorted by CPU usage.
4. [ ] Grab a **real** SSH auth log — the [OpenSSH dataset from loghub](https://github.com/logpai/loghub)
   is genuine brute-force noise (MITRE ATT&CK [T1110, Brute Force](https://attack.mitre.org/techniques/T1110/))
   — and produce a ranked per-source-IP count of the failed logins. (Reach for `grep`,
   `awk`, `sort`, `uniq` — the pipeline *is* the skill.)

## Success criteria — you're done when
- [ ] You can list every UID-0 account and everyone who can `sudo`.
- [ ] You can name the default SUID-root binaries and say why each matters if modified.
- [ ] Your one-liner prints a per-IP failed-login count.

## Deliverables
A short `linux-triage.md`: the privileged accounts, the SUID list, and the top failed-login
IPs — the notes you'd paste into an incident ticket.

## AI acceleration
Ask a model to explain any SUID binary it flags as unusual — then confirm with `man` and
your own judgment before acting.

## Connects forward
This is the host fluency Track 01 (privilege escalation) and Track 07 (host hardening)
assume, and the artifact-reading habit Track 03 (forensics) builds on.

## Marketable proof
> "Drop me on an unfamiliar Linux box and I can profile its users, privileged binaries,
> processes, and auth logs in minutes — by hand or scripted."

## Automate & own it
**Required.** Turn your by-hand triage into one reusable script (users + SUID + ranked
failed-logins). Have AI draft it, review every line, and commit it as `linux-triage.sh`.

## Stretch
- Turn the failed-login one-liner into a ranked top-5 with a threshold, then rewrite it in
  Python (a preview of Track 09).
