# Module 04 — Linux for Security

*Variant D · skill-first, breach as stakes. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *most of what you'll defend, attack, or investigate runs on Linux, and an investigation is just reading its files and logs well.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules
{ .module-meta }

## The hook — how a worm ate the internet with one password

In October 2016, a botnet called **Mirai** knocked a chunk of the US internet offline — Twitter,
Netflix, Reddit, and others went dark for hours when Mirai aimed a record-breaking flood of traffic at
Dyn, a major DNS provider. The botnet wasn't built from hacked servers or stolen zero-days. It was built
from **cameras and home routers** — hundreds of thousands of small Linux devices — and it took them over
with nothing more sophisticated than a list of about 60 **default username/password pairs**
(`admin/admin`, `root/12345`, and so on). Mirai's [released source code](https://github.com/jgamblin/Mirai-Source-Code)
shows the whole trick: scan the internet for an open SSH/telnet login, try the default-credential list,
and the moment one works you're *in* — you have a shell on a Linux box.

That's the uncomfortable lesson under this module. The devices ran Linux. The attacker's first act after
getting in was the same first act *you'll* perform as a defender: open a shell and look around. The
difference between a worm operator and an investigator isn't the access — it's what you do with the shell
and how well you can read what's there. Mirai's victims couldn't see they'd been taken. By the end of
this module you'll be the person who *can*.

## Objective

Operate confidently on a Linux command line and use core tools — the shell, file permissions, processes,
and the text-processing pipeline (`grep`/`awk`/`cut`/`sort`) — to investigate a compromised host: figure
out **who got in, how, and what they can now do**, then fold that hunt into a reusable triage script.

## The core idea

Two mental models carry almost all of Linux security, and both of them turn "investigation" into
"reading."

**Everything is a file.** Users live in a file (`/etc/passwd`). Who can become root lives in a file
(`/etc/group`, `/etc/sudoers`). Login attempts — every success and every failure — land as lines in a log
file (`/var/log/auth.log`). Even running processes and live kernel state show up as files under `/proc`.
Because it's all text, the *same* handful of tools reads all of it. There's no special "forensics app";
the forensics app is `grep` and your eyes. That's why text-processing isn't a chore you tolerate — it's
the core security skill on Linux, and the reason a worm operator and an incident responder use the exact
same commands.

**Permissions are the whole access-control story, in a few bits.** Every file carries `rwx` (read, write,
execute) for three audiences — its **user** (owner), its **group**, and **other** (everyone else) — which
is what `-rwxr-xr-x` in an `ls -l` listing is spelling out. On top of that sits one bit that matters far
out of proportion to its size: **SUID** (set-user-ID). A normal program runs with *your* privileges. A
SUID program runs with **its owner's** privileges instead — so a SUID-root binary runs as root no matter
who launches it. That's intentional and necessary for a few tools (`passwd` has to edit a root-owned
file), but it's also the seed of half of Linux privilege escalation: find an unexpected SUID-root binary
an attacker dropped, and you've found a backdoor that hands anyone root.

So an investigation is three reading passes over those files: **who's here** (accounts and who can become
root), **what can they do** (permissions and SUID), and **what happened** (the logs). The
`grep | awk | cut | sort | uniq` pipeline is how you turn a million log lines into the one fact that
matters — *which IP tried 200 passwords, and did any of them work?* This is the muscle memory every later
track assumes: when offense escalates privilege or forensics carves a host, it starts right here.

The judgment to carry: a model is a fast shell tutor and a great one-liner generator, but **verify before
you run.** Check flags against `man`, and never paste a generated command that touches files or
permissions — a wrong `rm` or `chmod` on a live box has no undo. The fluency is the point; AI accelerates
building it, it does not replace it.

## Learn (~3 hrs)

**The shell & the filesystem** — *learn to move and read; this carries the raw how-to.*
- [The Missing Semester — The Shell](https://missing.csail.mit.edu/2020/course-shell/) (~1 hr, do the exercises) — MIT's no-fluff intro to *thinking* in the shell, not memorizing commands. The exercises are the point.
- [Julia Evans — "Bite Size Linux"](https://wizardzines.com/zines/bite-size-linux/) (~30 min, free zine) — the clearest illustrated explanation of `rwx`, SUID, processes, and `/proc` anywhere. Read the permissions and SUID pages twice.

**Permissions & SUID — the privilege-escalation seed**
- [DigitalOcean — An Introduction to Linux Permissions](https://www.digitalocean.com/community/tutorials/an-introduction-to-linux-permissions) (~30 min) — read the SUID section slowly; it underpins half of privilege escalation, and the lab leans on it.
- [GTFOBins](https://gtfobins.github.io/) (~15 min, reference) — the catalog of how a misconfigured SUID binary becomes a root shell. Skim a few entries to see *why* an unexpected SUID file is a finding, not trivia.

**Text processing — the security power tool**
- [The Grymoire — Awk tutorial](https://www.grymoire.com/Unix/Awk.html) (~45 min, plus `man grep`) — the classic deep reference for the pipeline you'll live in for log triage. Pair it with `man grep`/`man sort`.

**The incident behind the module**
- [Krebs on Security — "Who Makes the IoT Things Under Attack?"](https://krebsonsecurity.com/2016/10/who-makes-the-iot-things-under-attack/) (~15 min) — the contemporaneous reporting on Mirai; read it for *how little* it took to own a Linux device at scale.

## Key concepts
- "Everything is a file": accounts, privilege, processes (`/proc`), and logs (`/var/log`) are all text you read with the same tools
- The filesystem hierarchy — why `/etc`, `/var/log`, and `/proc` are the first places you look
- Users, groups, and the permission model (`rwx` for user/group/other), plus root (UID 0) and `sudo`
- **SUID** (set-user-ID): a binary that runs as its *owner*, not the caller — the seed of Linux privilege escalation
- The text-processing pipeline (`grep`, `awk`, `cut`, `sort`, `uniq`) and reading `auth.log` to answer "who got in, how"

## AI acceleration
A model is a fast shell tutor — ask it to explain an unfamiliar SUID binary, decode a permission string,
or draft the `awk` field-extraction for a log line. The catch a beginner must internalize: it will
confidently produce a one-liner with the wrong field number (`$11` vs `$9` depends on the exact log
format) or a flag that means something else on your distro. **AI drafts → you verify against `man` and
the real data → you own the command.** Never run a generated command that deletes, moves, or `chmod`s
anything on a system you care about without reading every token first.
