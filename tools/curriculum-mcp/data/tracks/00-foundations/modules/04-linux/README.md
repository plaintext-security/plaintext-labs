# Module 04 — Linux for Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *most of what you'll defend, attack, or investigate runs on Linux.*

## Why this matters
Servers, containers, security tooling, and half an attacker's targets are Linux. The shell
is the universal interface, and the difference between *reading* a system and *guessing* at
it is fluency with a handful of core tools. This is the muscle memory every later lab
assumes — when Track 01 escalates privilege or Track 03 carves a filesystem, it starts
here.

## Objective
Operate confidently on a Linux command line and use core tools to investigate a host's
users, processes, files, and logs.

## The core idea
Most of what you'll defend, attack, or investigate runs on Linux, and the shell is the universal
interface — so the gap between *reading* a system and *guessing* at it is just fluency with a handful
of tools. Two mental models carry most of the weight. **"Everything is a file":** processes, devices,
even live kernel state (`/proc`) all appear as files you read with the same tools — which is why
text-processing is a security superpower, not a chore. And the **permission model** (`rwx` for
user/group/other, plus SUID/SGID) is the entire OS access-control story in a few bits — with SUID
specifically being the seed of half of Linux privilege escalation: a file that runs as *its owner*,
not as you.

The text-processing pipeline (`grep | awk | cut | sort | uniq`) is what you'll actually live in — log
triage, parsing tool output, finding the one line that matters among a million. It's worth real reps
because every later track (privesc, forensics, detection) comes back to "read this host's users,
processes, files, and logs, fast."

The judgment: a model is a quick shell tutor and one-liner generator, but verify before you run —
check flags against `man`, and never paste a generated command that touches files or permissions
without reading it, because a wrong `rm` or `chmod` on a live box doesn't have an undo. The fluency is
the point; AI accelerates building it, it doesn't replace it.

## Learn (~3 hrs)

**The shell & the filesystem**
- [The Missing Semester — The Shell](https://missing.csail.mit.edu/2020/course-shell/) — MIT's no-fluff intro to thinking in the shell; do the exercises.
- [The Linux Command Line — Bash Basics](https://linuxcommand.org/lc3_learning_the_shell.php) — bite-sized and hands-on introduction to the shell; covers pipes, redirection, and basic commands.
- [Filesystem Hierarchy Standard](https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html) — skim it so `/etc`, `/var`, and `/proc` stop being mysterious.

**Permissions, processes & users**
- [Julia Evans — "Bite Size Linux"](https://wizardzines.com/zines/bite-size-linux/) — the clearest explanation of `rwx`, SUID, and processes anywhere.
- [DigitalOcean — An Introduction to Linux Permissions](https://www.digitalocean.com/community/tutorials/an-introduction-to-linux-permissions) — read the SUID section twice; it underpins half of privilege escalation.

**Text processing (the security power tool)**
- [The Grymoire — awk and sed tutorials](https://www.grymoire.com/Unix/Awk.html) plus `man grep` — the classic deep references; you'll live in these for log triage.

## Key concepts
- The filesystem hierarchy and "everything is a file"
- Users, groups, and permission bits (`rwx`, SUID/SGID)
- Processes and `/proc`
- Text-processing pipelines (`grep`, `awk`, `cut`, `sort`, `uniq`)
- Where logs live (`/var/log`) and how to read them

## AI acceleration
A model is a fast shell tutor — ask it to explain an unfamiliar command or draft an `awk`
one-liner. Verify before you run: check flags against `man`, and never paste a generated
command that touches files or permissions without reading it first.
