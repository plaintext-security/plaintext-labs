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

A fourth vector — **the real PwnKit CVE-2021-4034** — runs in a separate
Vulhub environment (see Vector 4 below): a known-vulnerable `polkit`/`pkexec`
build, not a planted misconfiguration.

## Scenario

You've obtained an initial shell on the application server as
`appuser` — a low-privilege account. The goal is to escalate to root by
enumerating the system and exploiting the vectors you find. Three are deliberate
misconfigurations (SUID, sudo, writable cron — the "boring but reliable" classes
real engagements actually live on); the fourth is a genuine, named CVE
(**CVE-2021-4034 / PwnKit**) against a truly vulnerable component.

> **Authorization note:** Only escalate privileges on systems you own or
> have explicit written authorisation to test. This container and the Vulhub
> PwnKit environment are intentionally vulnerable; run them inside the provided
> lab only.

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

5. [ ] **Vector 4 — exploit the real CVE-2021-4034 (PwnKit).** The three vectors above are
   planted misconfigurations; this one is a genuine, named CVE against a truly vulnerable
   component. **What the bug is:** polkit's `pkexec` mishandles an `argc == 0` invocation and
   ends up treating an attacker-controlled environment variable as a program path —
   re-executing it with root privileges. The result is a clean local root from any
   unprivileged user, with no misconfiguration required.

   Spin it up from the shared dataset cache rather than re-cloning Vulhub by hand. From inside
   the labs tree, source `lib/fetch.sh` and `fetch_repo vulhub` to get a cached Vulhub clone;
   the environment lives at `<vulhub-clone>/polkit/CVE-2021-4034`:

   ```bash
   # from anywhere inside plaintext-labs/
   . "$(d=$PWD; while [ ! -f "$d/lib/fetch.sh" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/lib/fetch.sh"
   VULHUB=$(fetch_repo vulhub)
   cd "$VULHUB/polkit/CVE-2021-4034"
   cat README.md   # follow THIS env's instructions, not a plain compose
   ```

   > **Important — this vector is a QEMU VM, not the Debian container.** The underlying
   > `argc == 0` kernel behaviour that PwnKit relies on was later patched, so modern Docker
   > hosts can't reproduce the bug in a plain container. The Vulhub `polkit/CVE-2021-4034`
   > environment therefore boots a **QEMU VM (Ubuntu 20.04, polkit 0.105)** to provide a
   > genuinely vulnerable target. `make up`/startup for *this* vector follows the steps in that
   > directory's `README.md` (it launches the VM) — it does **not** run in the same Debian
   > container as Vectors 1–3. Inside the VM, build and run the public PwnKit PoC and confirm
   > `id` returns `uid=0(root)`.

6. [ ] Explain the difference between:
   - `uid=0(root)` (real uid is root)
   - `euid=0(root)` (effective uid is root, via SUID)
   - Why does `sh -p` matter for the SUID exploit?

## Success criteria — you're done when

- [ ] You enumerated all three misconfiguration vectors (SUID, sudo, writable cron) from the appuser shell.
- [ ] You gained root (uid=0 or euid=0) via at least one misconfiguration vector.
- [ ] You exploited the real CVE-2021-4034 (PwnKit) against vulnerable polkit and confirmed `uid=0(root)`.
- [ ] You can explain the exact misconfiguration and the remediation for each planted vector, and what made polkit vulnerable to PwnKit.
- [ ] You know what GTFOBins is and how to use it to look up an escalation technique.

## Deliverables

`linux-privesc.md`: the three misconfiguration vectors (how found, what misconfiguration,
GTFOBins entry) plus the real CVE-2021-4034 (PwnKit) exploitation (what the bug is, the
vulnerable polkit version, the PoC used), the proof-of-root command output for each, and the
remediation.

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
> misconfigurations, and writable cron scripts via GTFOBins, plus the real
> CVE-2021-4034 (PwnKit) against vulnerable polkit — and I can map each vector
> to its defensive remediation."

## Stretch

- Exploit a second real local-root CVE to contrast PwnKit's technique: e.g.
  **DirtyCow (CVE-2016-5195)** (copy-on-write race → write to read-only memory)
  or **Dirty Pipe (CVE-2022-0847)**. Note why kernel/system-level CVEs like these
  are the "last resort" — less stable, more noise — versus the planted
  misconfiguration vectors.
- Run `lynis audit system` inside the container and compare its output to your
  manual enum. Which findings overlap? Which does lynis miss?
