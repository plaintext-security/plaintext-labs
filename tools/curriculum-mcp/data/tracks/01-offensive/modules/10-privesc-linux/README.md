# Module 10 — Privilege Escalation: Linux

*Type 2 · Misconception Reveal — enumerate a Linux host and escalate to root to reveal that privesc is misconfiguration, not exploits — the same list a CIS benchmark audits, read from the attacker's end. (Secondary: Detonate & Detect — that hardening/detection bridge.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Offensive Security** — *a shell is rarely root; this is how you get there.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
Initial access usually lands you as a low-privilege user. Privilege escalation — turning that
foothold into root — is what makes an intrusion serious, and it almost always comes from
misconfiguration: a writable SUID binary, a permissive sudo rule, a hijackable cron job. When it
isn't a misconfig it's an unpatched local flaw like **PwnKit ([CVE-2021-4034](https://nvd.nist.gov/vuln/detail/CVE-2021-4034))**
— a memory-corruption bug in polkit's `pkexec` that gives any local user instant root on
essentially every Linux distro, and sat undiscovered for over a decade. Finding these systematically
(and, as a defender, removing them) is core to both attack and hardening.

## Objective
Enumerate a Linux host for privilege-escalation vectors and exploit one to gain root in your
lab.

## The core idea
Initial access almost never lands you as root — it lands you as `www-data` or some service account,
and privilege escalation is turning that into root, which is what makes an intrusion genuinely serious.
The crucial mental shift: Linux privesc is overwhelmingly about **misconfiguration, not exploits.** The
system *hands* you root when you find the one thing an admin set up wrong — a SUID binary that runs as
root but will spawn a shell, a too-generous `sudo` rule, a cron job running a script you can write, a
writable `PATH` entry. So the workflow is **enumerate first, exploit second**: inventory the
misconfigurations before you try anything.

GTFOBins makes this concrete — it's the catalog of how ordinary Unix binaries (`find`, `vim`, `tar`)
become a root shell when they run with privilege in the wrong config. The other branch is the unpatched
local exploit: PwnKit (CVE-2021-4034) is the canonical example — a SUID-root binary present by default
on nearly every distribution, exploitable with no special config, which is why "is this box patched
against the famous local-root CVEs?" is part of every enumeration. Tools like `linpeas` and `pspy`
automate the enumeration so you're not checking every vector by hand, but they only *gather* — you
still read the output and judge which lead is real.

The judgment, and the hardening bridge: every vector here is something the defensive side *removes* —
this is the same list a CIS benchmark or a hardening script audits, read from the attacker's end (do
this consciously and you can hand a defender the exact fix). A model reads `linpeas` output and proposes
the likely vector fast, but it will also point confidently at a dead end, or at a kernel exploit that
crashes the box — kernel exploits are the last resort precisely because they're unstable. Verify the
vector against GTFOBins by hand before you pull the trigger.

## Learn (~4 hrs)

**The vectors**
- [GTFOBins](https://gtfobins.org/) — the canonical catalog of Unix binaries that can be abused to escalate; you'll use this constantly.
- [Linux Privilege Escalation using `sudo -l` — GTFOBins (video)](https://www.youtube.com/watch?v=HnlYElVhXpo) — a worked example of turning one misconfigured sudo rule into root.
- [Qualys advisory — PwnKit: local privilege escalation in polkit's pkexec (CVE-2021-4034)](https://www.qualys.com/2022/01/25/cve-2021-4034/pwnkit.txt) — the original disclosure; read it for how a SUID binary's argument handling becomes root, the canonical unpatched-local-exploit case.

**Where it sits**
- [MITRE ATT&CK — Privilege Escalation (TA0004)](https://attack.mitre.org/tactics/TA0004/) — the tactic and its techniques.

## Key concepts
- Enumeration first (what `linpeas`/`pspy` automate — and what they look for)
- SUID/SGID binaries and GTFOBins
- sudo misconfigurations
- Writable cron jobs, PATH, and services
- Unpatched local-root CVEs (e.g. PwnKit / CVE-2021-4034 in pkexec) vs. misconfiguration
- Kernel exploits — and why they're the last resort

## AI acceleration
A model reads `linpeas` output and suggests the likely vector fast — a real accelerator. But
it also confidently points at a dead end or a kernel exploit that crashes the box. Verify the
vector by hand (check GTFOBins) before you pull the trigger.
