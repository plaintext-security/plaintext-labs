# Lab 10 — Escalate to Root on Linux

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/10-privesc-linux
make up
```

The container is a Debian host with three planted misconfigurations:
SUID bit on `find`, a NOPASSWD sudo rule for `find`, and a world-writable
cron script running as root. You start as `appuser` (uid=1001).

## Scenario

You've obtained an initial shell on Meridian Financial's application server as
`appuser` — a low-privilege account. The goal is to escalate to root by
enumerating the system and exploiting one of the misconfigurations.

> **Authorization note:** Only escalate privileges on systems you own or
> have explicit written authorisation to test. This container is intentionally
> misconfigured; run it inside the provided lab only.

## Do

1. [ ] Shell into the container as `appuser` and enumerate the host by hand to find your
   escalation vectors — before looking at any worked answer. (`make shell`, then
   `su - appuser`, password `appuser`.) Hunt SUID binaries, your sudo rights, and writable
   scheduled jobs. (Which commands surface each? Three misconfigurations are planted —
   find all three.) `make demo` runs the validated exploit for all three; save it to check
   your enumeration *after* you've done it yourself.

2. [ ] For Vector 1 (SUID binary): look the binary up on
   [GTFOBins](https://gtfobins.org/), work out the invocation that spawns a shell
   with its elevated privileges, run it, and confirm `id` shows you reached root. (Why does
   the `-p` flag matter for a SUID shell?)

3. [ ] For Vector 2 (sudo NOPASSWD): your `sudo -l` output names a binary you can run as
   root without a password. Turn that into a root shell or root command execution via its
   GTFOBins technique. Why is this vector higher-confidence than the SUID one?

4. [ ] For Vector 3 (writable scheduled job): confirm the script is writable, work out what
   you'd append to have it execute your code as root, and explain why this is a persistence
   vector, not just one-shot escalation.

5. [ ] Explain the difference between:
   - `uid=0(root)` (real uid is root)
   - `euid=0(root)` (effective uid is root, via SUID)
   - Why does `sh -p` matter for the SUID exploit?

## Success criteria — you're done when

- [ ] You enumerated all three vectors (SUID, sudo, writable cron) from the appuser shell.
- [ ] You gained root (uid=0 or euid=0) via at least one vector.
- [ ] You can explain the exact misconfiguration and the remediation for each.
- [ ] You know what GTFOBins is and how to use it to look up an escalation technique.

## Deliverables

`linux-privesc.md`: the three vectors (how found, what misconfiguration, GTFOBins entry),
the proof-of-root command output, and the remediation for each.

## Automate & own it

**Required.** Write `enum.py` that:
- Finds SUID binaries in common paths
- Reads `/etc/sudoers` and parses NOPASSWD rules
- Reads `/etc/crontab` and checks write permissions on scripts
- Outputs a priority-ranked shortlist of vectors

AI drafts the script; you cross-check each result against GTFOBins and verify
by hand before trusting it. Commit `enum.py` and `linux-privesc.md`.

## AI acceleration

Paste your `sudo -l` and `find / -perm -u=s` output to a model and ask it to
shortlist the highest-confidence vector and the GTFOBins technique. Then verify
against GTFOBins yourself — the model shortlists; you confirm. Models often
surface kernel exploits prematurely (they crash boxes); prefer misconfiguration
vectors for stability.

## Connects forward

Root on one host enables the lateral movement in module 12 (pivoting). The
defensive inverse is Track 07 (endpoint hardening) — each vector here maps
directly to a CIS benchmark check or a lynis finding.

## Marketable proof

> "I enumerate and escalate privilege on Linux — SUID binaries, sudo
> misconfigurations, and writable cron scripts — using GTFOBins, and I can
> map each vector to its defensive remediation."

## Stretch

- Exploit **PwnKit (CVE-2021-4034)** in a lab container: run a vulnerable
  `pkexec` version and demonstrate how the bug turns a heap corruption into root
  without any planted misconfiguration. Note why kernel/system-level CVEs like
  this are the "last resort" — less stable, more noise.
- Run `lynis audit system` inside the container and compare its output to your
  manual enum. Which findings overlap? Which does lynis miss?
