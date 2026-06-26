# Data provenance — 04-linux SSH auth log

## The log you analyze: a REAL public SSH brute-force capture

The primary dataset for this lab is the **loghub OpenSSH** log — a real, public capture
of an internet-facing `sshd` under sustained credential brute-force.

- **Source:** logpai/loghub — <https://github.com/logpai/loghub> (OpenSSH dataset)
- **File fetched:** `OpenSSH_2k.log`, a 2,000-line excerpt of a real `sshd` log
  (the full `OpenSSH_2k.log` / `OpenSSH.log` capture is ~655k lines).
- **Direct URL (used by `make fetch-data`):**
  <https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log>
- **What it shows:** thousands of `Failed password` / `Invalid user` lines from many
  source IPs against common usernames (`root`, `admin`, `test`, …) — i.e. exactly the
  T1110 Brute Force noise this module is about. Real attacker IPs, real `LabSZ` host.
- **Citation:** Jieming Zhu et al., *"Tools and Benchmarks for Automated Log Parsing"*
  (ICSE-SEIP 2019); loghub is the companion dataset collection.

## Why `make fetch-data` instead of vendoring the file

The real log is fetched at lab time rather than committed here, so the repo stays free of
bulk third-party data and the learner sees the genuine, current upstream artifact. The tiny
`auth_sample.log` that *is* committed is only a fallback/format example for offline use.

## The one synthetic addition: `compromise_overlay.log`

The real loghub log is **almost entirely brute-force noise.** It contains exactly one
successful login — `Accepted password for fztu from 119.137.62.142` — but that source IP
never appears as a *failure*, so it is a **benign** login, not a compromise. The lab's
central lesson (a success from an IP that was *also* brute-forcing = compromise) therefore
has no positive example in the real data. To supply one, the demo appends two clearly-labeled
overlay lines: an `Accepted password` from the single most prolific brute-force source IP in
the real log (`187.141.143.180`). The learner then has a clean contrast — benign `fztu`
(clean IP) vs. compromised `jsmith` (80 prior failures from the same IP). See the header of
`compromise_overlay.log`. This overlay is the only non-real data in the lab.

The synthetic success lands the account **`jsmith`** — a planted on-box user with a
`NOPASSWD:ALL` sudoers entry (see `Dockerfile`). This is deliberate: it makes the three
triage passes interlock. The brute-forced account (log) is the one with total sudo
(accounts), and the **root-owned SUID backdoor** the Dockerfile plants at
`/usr/local/bin/.cache-helper` is what that access was used to establish (the SUID sweep).
So "who got in → how → what they can now do" resolves end to end instead of dead-ending on a
username that exists only in the log.

## RUNNER-VALIDATION NEEDED

`make fetch-data` reaches the network (GitHub raw) and has **not** been run in the authoring
environment. Validate on a Linux runner: `make fetch-data && make demo` should fetch
`OpenSSH_2k.log`, overlay the compromise line, and print a ranked failed-login table with the
overlaid `Accepted` from `187.141.143.180` flagged as "ALSO a brute-force source."
