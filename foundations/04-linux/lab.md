# Lab 04 — Who Got In: Triaging a Compromised Linux Host

*Variant D · skill-first. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo: an Ubuntu 22.04 container
with planted accounts, a `sudoers` entry, and a real-shaped SSH auth log to read.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/foundations/04-linux
make up      # build + start the container
make shell   # drop into the container to run the commands yourself
make demo    # show the expected triage output, only after you've tried
make down    # stop when done
```

> Only run these commands against systems you own or this throwaway container. Reading the provided log
> and the container's own files touches nothing outside the lab — but build the habit now of asking
> "am I authorized?" before you investigate any host.

## Scenario
You've been handed shell access to a small Linux server (a bastion host) after an alert fired. The auth
log in `data/auth_sample.log` is what the system recorded. Something got in. Your job is the first job of
every investigation: profile the box — **who's here, what can they do, what happened** — and render a
plain-language verdict: **who got in, how, and what they can now do.** These are the same three reading
passes from the module: accounts, permissions, logs.

## Do
Derive the commands yourself — the Learn resources and `man` are how. State the goal; you find the
keystrokes. Each pass feeds the next.

1. [ ] **Who's here.** List every local account, then narrow to the ones that matter: every **UID-0**
   account (those *are* root) and everyone who can become root via `sudo`. (Where do users live? Which
   file or group grants `sudo`, and is anything `NOPASSWD`?) Note any account whose sudo rights look
   surprisingly broad — that's a privilege you'll want to tie to the log later.

2. [ ] **What can they do — the SUID sweep.** Find every file on the system that runs with its owner's
   privileges, not yours. (Which permission bit is that, and how do you search the *whole* filesystem
   for it in one command?) For each hit, ask: is this a normal system binary, or something that
   shouldn't be SUID-root? (When one looks wrong, check it against [GTFOBins](https://gtfobins.github.io/).)

3. [ ] **What's running.** Show the running processes ranked by CPU. (You're building the reflex —
   on a real box this is where a rogue miner or a reverse shell would stand out.)

4. [ ] **What happened — read the log.** This is the heart of it. From `data/auth_sample.log`, build a
   pipeline that produces a **ranked count of failed logins per source IP** (reach for `grep`, `awk`,
   `sort`, `uniq` — the pipeline *is* the skill). Then answer the questions the count alone won't:
   - Which IPs are clearly **brute-forcing** (many failures, many usernames)?
   - Did **any** login *succeed* from an IP that was failing moments earlier? (Compare your failed-IP
     list against the `Accepted password` lines — a success from a brute-force source is a compromise,
     not a coincidence.)
   - Which **account** did that successful login use — and cross-reference pass 1: **what can that
     account now do?**

5. [ ] **Render the verdict.** In two or three sentences: name the IP that got in, the account it
   compromised, the technique (credential brute-force, MITRE ATT&CK
   [T1110](https://attack.mitre.org/techniques/T1110/)), and why it matters — what that account's
   privileges mean for the blast radius. This is the line you'd paste at the top of an incident ticket.

## Success criteria — you're done when
- [ ] You can list every UID-0 account and everyone who can `sudo`, and you flagged the `NOPASSWD` one.
- [ ] You can name the SUID-root binaries and say in one sentence why an *unexpected* one is a backdoor.
- [ ] Your one-liner prints a per-IP failed-login count, ranked.
- [ ] You identified the **source IP that succeeded after brute-forcing**, the **account** it landed,
  and tied that account to its sudo rights — i.e. you can state *who got in, how, and what they can do.*

## Deliverables
A short `linux-triage.md` written like an incident note: the privileged accounts, the SUID list, the
ranked failed-login IPs, and — at the top — the two-sentence verdict (who got in, how, blast radius).
Commit it alongside your script. Do **not** commit the container's files, the raw log, or anything
generated.

## Automate & own it
**Required.** Fold your by-hand hunt into one reusable triage tool, `linux-triage.sh`: it should print
the privileged accounts, the SUID-root list, and the **ranked failed-login IPs**, and flag any IP that
appears in *both* the failed list and an `Accepted` line (the compromise signal). Start from your pass-4
one-liner; that pipeline *is* the core of the script. Have a model draft it, then **review every line** —
confirm each field number against a real log line and each flag against `man` — and commit it. This is
the triage you'd run on the next box in seconds instead of minutes.

## AI acceleration
Ask a model to explain any SUID binary your sweep flags as unusual, or to draft the `awk` that extracts
the source IP from an `auth.log` line — then confirm the field number against an actual line and `man`
before trusting it. A wrong field number silently ranks the wrong column.

## Connects forward
This host fluency is what offense's privilege-escalation work and host-hardening modules assume, and the
artifact-reading habit (read the log, render the verdict) is the spine of forensics and detection. The
triage script is your first entry in the Phase 2 toolkit and a preview of the scripting module.

## Marketable proof
> "Drop me on an unfamiliar Linux box and I'll profile its users, privileged binaries, processes, and
> auth log in minutes — and tell you who got in, how, and what they can reach — by hand or scripted."

## Stretch
- Add a time-window filter to your one-liner: count failures *per IP per minute* to separate a slow,
  patient attacker from a noisy one.
- Rewrite `linux-triage.sh` in Python (a preview of the scripting module) so the compromise flag is a
  proper function with a test against the bundled log.
