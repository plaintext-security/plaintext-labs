# Data provenance — 10-scripting SSH auth log

This module reuses the **same real public SSH brute-force capture as module 04** so the tool you
build here parses the exact log you triaged by hand there.

- **Source:** logpai/loghub — <https://github.com/logpai/loghub> (OpenSSH dataset)
- **File fetched by `make fetch-data`:** `OpenSSH_2k.log`, a 2,000-line excerpt of a real
  internet-facing `sshd` log (full capture ~655k lines).
- **Direct URL:**
  <https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log>
- **What it is:** thousands of `Failed password` / `Invalid user` lines from many source IPs —
  genuine T1110 brute-force noise, the scale problem this module exists to solve.
- **Citation:** Jieming Zhu et al., *"Tools and Benchmarks for Automated Log Parsing"* (ICSE-SEIP 2019).

The committed `ssh_auth.log` is a tiny offline fallback/known-answer fixture; the real, larger
`OpenSSH_2k.log` is fetched at lab time and stays out of the repo.

## RUNNER-VALIDATION NEEDED

`make fetch-data` reaches GitHub raw and has **not** been run in the authoring environment. Validate
`make fetch-data && make demo` on a Linux runner — the demo should rank source IPs from the real log.
