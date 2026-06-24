# Track 00 — Foundations

The bedrock — learned by autopsying the breaches that make each fundamental matter. Every module opens on
a real, public incident, has you build the actual skill (set up a lab, read a packet, use git), and ends
with you explaining what failed and turning the work into a small reviewable script. Set up a safe lab,
work on Linux *and* Windows, read the network and the web, handle data and crypto, automate with Python,
and work in the open with git. Build this floor solid and everything above it gets easier.

## How this track works

This is the beginner track, so it's **skill-first**: the breach is the hook and the stakes, not a horror
story. The recurring move, lightened for beginners:

1. **Predict** — only where a beginner's intuition is reliably *wrong* (base64 is not encryption; deleting
   a secret in the next commit does not remove it). Those wrong guesses are the best teaching moments here.
2. **Do** — build the actual skill against a *real-shaped* artifact (a real log, a real capture, a real
   password-dump scheme).
3. **Explain** — say in your own words what happened and which principle or control failed.
4. **Own it** — turn the manual steps into a small reviewable script: **AI drafts → you review every line
   → you own it.**

## What you'll be able to do
- Set up an isolated, reproducible lab and work fluently with containers.
- Operate both Linux and Windows from the command line for security tasks.
- Read network traffic, HTTP, and the encodings security data actually shows up in.
- Explain the cryptographic primitives that secure modern systems — and where they fail.
- Automate with Python, work in the open with git, and threat-model before you touch a tool.

## Modules

| # | Module | Real anchor | What you'll build / explain | OSS tools |
|---|--------|-------------|------------------------------|-----------|
| 01 | [Security First Principles](modules/01-security-principles/README.md) | Equifax 2017 | a "principle autopsy" mapping each failure to CIA/AAA/defense-in-depth | — |
| 02 | [Building a Safe Lab](modules/02-lab-setup/README.md) | VENOM / malware-lab discipline | an isolated lab, captured as a rebuild-from-zero script | VirtualBox, Docker |
| 03 | [Docker & Containers](modules/03-docker/README.md) | exposed Docker-API cryptojacking | run/build/inspect; the isolation model and its limits | `docker` |
| 04 | [Linux for Security](modules/04-linux/README.md) | Mirai 2016 / SSH brute-force | investigate a compromised host from its logs | `bash`, `coreutils` |
| 05 | [Windows for Security](modules/05-windows/README.md) | Emotet-style persistence | triage an intrusion from event logs, registry, services | `powershell` |
| 06 | [Networking Fundamentals](modules/06-networking/README.md) | SUNBURST DNS C2 | walk a capture; spot the beacon hiding in DNS | `tcpdump`, `wireshark` |
| 07 | [Web & HTTP Fundamentals](modules/07-web-http/README.md) | Firesheep 2010 | sessions, cookies, and the header that stops the hijack | `curl` |
| 08 | [Data & Encoding](modules/08-data-encoding/README.md) | base64 PowerShell malware | decode a layered blob — and learn encoding ≠ encryption | `cyberchef`, `jq` |
| 09 | [Cryptography Basics](modules/09-cryptography/README.md) | Adobe 2013 | hashing vs encryption, salt, why "encrypted" wasn't safe | `openssl` |
| 10 | [Scripting & Automation](modules/10-scripting/README.md) | a real IOC list / log at scale | turn manual analysis into a reviewable Python tool | `python3` |
| 11 | [Version Control & Working in the Open](modules/11-version-control/README.md) | Toyota 2022 key leak | git history, and why deleting a secret doesn't remove it | `git` |
| 12 | [Threat Modeling](modules/12-threat-modeling/README.md) | Target 2013 | trust boundaries + STRIDE on the lab you built | — |

*Anchors are real, public incidents and primary sources.*

## Phases & projects

Twelve modules in three phases; each ends in a **project** that integrates its modules.

- **Phase 1 · Lab & first principles (01–03)** — **Project:** stand up your isolated, reproducible lab
  (VM + containers), captured as a rebuild-from-zero script, and threat-model it.
- **Phase 2 · Hosts & networks (04–07)** — **Project:** a scripted triage toolkit that profiles a Linux
  *and* a Windows host (users, SUID/services, logon events) and pulls the DNS + handshake from a real capture.
- **Phase 3 · Data, crypto, automation & git (08–12)** — **Project (the capstone):** a Python "foundations
  toolkit" repo that decodes a real artifact, checks crypto the right way, and parses a real log, committed
  with secret hygiene and a STRIDE model.

## Who this is for
Complete beginners and anyone solidifying fundamentals before a specialisation track. No prior security
experience assumed.

## Capstone — "Prove the literacy on real artifacts"
Stand up your isolated lab and a portfolio repo, then prove the core literacy in one committed artifact:
capture and walk an HTTP exchange end to end (DNS → TCP handshake → TLS), **decode a real layered encoded
blob by committed script** (not just CyberChef clicks), check crypto the right way (a salted hash, not
ECB), parse a real log, and threat-model the little system you built. **Deliverable:** a `foundations/`
folder in your git repo with the capture write-up, the decode script, the crypto check, and a one-page
STRIDE model — your first portfolio piece.

The starter scaffold and acceptance checks live in
[`plaintext-labs/foundations/capstone/`](https://github.com/plaintext-security/plaintext-labs/tree/main/foundations/capstone).

### Capstone rubric
Grade your `foundations/` folder against this. **Proficient is the bar to ship; exemplary is the portfolio piece.**

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Packet-capture walk-through** | layers conflated (DNS/TCP/TLS) | DNS, the handshake, and the TLS hello each identified by packet number and explained in your words | adds the *why* — SNI, cleartext-vs-encrypted after ClientHello, one security header — tied to the RFC |
| **Decoding the blob** | one layer peeled; tool used as a black box | all layers decoded, each encoding named in order | decoded by a committed script, with how you recognised each layer (encoding ≠ encryption) |
| **Crypto checked right** | uses a bare/unsalted hash, or conflates hashing & encryption | a salted hash + a verify step, with why ECB/unsalted fails (the Adobe lesson) | also verifies a cert/TLS chain and explains it |
| **STRIDE model** | assets only, or generic threats | one page mapping your lab's trust boundaries to STRIDE with a concrete threat each | threats ranked, each with a mitigation, referencing components you built (the Target lesson) |
| **Secret & git hygiene** | `.pcap`/keys committed, or history dirty | no captures/keys/secrets in history; `.gitignore`; clean commits | pre-commit secret scan wired in; commits tell the build story |
| **Reproducibility** | steps not written down | a reader can reproduce each result | one `make`/script rebuilds the lab and re-runs the decode from zero |

## AI & automation
Automation and AI are assumed from day one — but as accelerators, not substitutes for understanding. Use
a model to explain a capture, draft a parsing script, or quiz you on a concept; then verify it against the
primary source (the RFC, the man page, the breach report). The standing posture: **AI drafts → you review
→ you own it.**

## Standards & further reading
- The relevant RFCs (TCP, DNS, HTTP, TLS) and `man` pages — the primary sources this track curates
- MITRE ATT&CK (for the techniques behind each anchor breach)
- Breach anchors: Equifax 2017, Adobe 2013, Target 2013, SolarWinds/SUNBURST, Mirai, Firesheep, Toyota 2022
