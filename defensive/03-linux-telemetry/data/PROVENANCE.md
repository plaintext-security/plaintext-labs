# Data provenance — Lab 03 (Linux Telemetry)

This lab teaches two real things: reading **auditd** event history and generating it yourself. The
committed seed lets `make demo` run offline; the two paths below get you genuine data.

## Real dataset 1: loghub Linux_2k.log (syslog)

- **Dataset:** loghub — Linux (`Linux_2k.log`)
- **Source URL (verified):** https://raw.githubusercontent.com/logpai/loghub/master/Linux/Linux_2k.log
- **Repository:** https://github.com/logpai/loghub
- **License:** loghub datasets are released for research/educational use (see the loghub repo / its
  Zenodo record). Attribute loghub on reuse.
- **What it contains:** 2000 lines of a genuine Linux system log from a host named `combo` —
  real `sshd`/`pam_unix` authentication failures from live scanning hosts, `su` sessions, and
  kernel/service messages. It is *syslog*, not auditd, so it complements (does not replace) the
  auditd seed: a real example of the host log stream auditd sits alongside.
- **How `make fetch-data` retrieves it:**
  `curl -fsSL <source URL> -o data/Linux_2k.log` (file is gitignored; pull it locally).

## Real dataset 2: generate genuine auditd telemetry with Atomic Red Team

The most honest way to get real auditd execution records is to produce them. On a host/VM you own:

1. Load the lab's audit rules: `sudo auditctl -R data/audit.rules`
   (captures `execve`, sensitive-file access, and privileged-command execution).
2. Run an Atomic Red Team test that maps to one of those rules. Recommended:
   - **T1136.001 — Create Account: Local Account**
     https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1136.001
     (a Linux test creates a local account via `useradd` — the exact action the committed seed's
     `useradd evil_backdoor` event represents, now generated for real).
   - Run with [Invoke-AtomicRedTeam](https://github.com/redcanaryco/invoke-atomicredteam) or by
     following the test's `T1136.001.md` manually.
3. Pull your real events: `sudo ausearch -k execve_watch` (or `-k user_mgmt` / `-k sensitive_file`),
   save them, and analyze with `python3 demo.py` (point `AUDIT_LOG` at your capture).

- **Atomic Red Team repo (verified):** https://github.com/redcanaryco/atomic-red-team
- **License:** MIT.

## Committed seeds

- `audit_events.txt` — a small, format-faithful auditd capture (neutral hostnames; an `execve`
  privilege-escalation + sensitive-file sequence) so `make demo` parses real auditd record types
  (`SYSCALL`/`EXECVE`/`PATH`) deterministically offline.
- `audit.rules` — the baseline auditd ruleset to deploy on a real host (used in path 2 above).

These seeds are teaching samples; run `make fetch-data` and/or the Atomic Red Team test above for
genuine telemetry.

## Citation

> loghub: Jieming Zhu et al., "Tools and Benchmarks for Automated Log Parsing," ICSE 2019 (SEIP),
> https://github.com/logpai/loghub. Atomic Red Team (Red Canary, MIT):
> https://github.com/redcanaryco/atomic-red-team
