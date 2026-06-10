# Module 01 — Reconnaissance & OSINT

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *the engagement starts here; the wider the attack surface you find, the more there is to test.*

## Why this matters
You can't attack what you can't see. Recon — passive OSINT and active mapping — is where
every real engagement and bug-bounty hunt begins, and the operators who find the most
surface find the most bugs. Done carelessly it's also where you wander out of scope and into
legal trouble, so disciplined, authorized recon is a skill in itself.

## Objective
Map a target's external attack surface from public information — domains, hosts,
technologies, and exposed services — without touching anything out of scope.

## The core idea
You can't attack what you can't see, and the size of your map sets the size of your opportunity.
Recon is building that map — and the discipline that separates a professional from someone running
tools is the **passive/active line**. Passive recon (certificate-transparency logs, DNS, public
records, leaked credentials, code repos) never touches the target: invisible, legal almost anywhere,
and surprisingly rich. Active recon (resolving hosts, probing) makes contact and can put you out of
scope — or into legal trouble. The mental model: you're reconstructing an organisation's
externally-visible footprint *the way the organisation itself has lost track of it* — forgotten
subdomains, shadow IT, the dev box someone exposed "just for a minute" in 2023.

That last point is the whole game. The attack surface is almost always bigger than the target
believes, because nobody keeps an accurate inventory of what they expose — asset management is a
genuinely hard problem on the defensive side too. Recon is the hunt for the assets that fell off the
inventory. Certificate Transparency is the cheat code here: every TLS certificate is logged publicly,
so every subdomain anyone ever got a cert for is discoverable without sending the target a single
packet.

The judgment that matters: **scope is what turns recon from a skill into a liability.** "Passive"
does not automatically mean "in scope," and a model will happily synthesise a tidy attack-surface map
that includes a hallucinated subdomain or one outside your authorisation. Treat AI output as *leads
to verify* — does it resolve? is it in scope? — never as confirmed assets. Anyone can run `amass`;
the value is the operator who confirms, contextualises, and stays in bounds.

## Learn (~3 hrs)

**Methodology**
- [The Bug Hunter's Methodology v4 — Recon Edition (Jason Haddix, ~50 min)](https://www.youtube.com/watch?v=p4JgIu1mceI) — the canonical talk on how real hunters map an attack surface; watch once, then keep as a reference.
- [MITRE ATT&CK — Reconnaissance (TA0043)](https://attack.mitre.org/tactics/TA0043/) — the taxonomy of recon techniques you'll map findings to.

**Sources & tooling**
- [OSINT Framework](https://osintframework.com/) — a navigable map of open-source intelligence sources.
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) — read the **Information Gathering** chapter for web-specific recon.

## Key concepts
- Passive vs active reconnaissance (and why the line matters legally)
- Subdomain enumeration (DNS, certificate transparency)
- Technology fingerprinting
- OSINT: people, emails, leaked credentials, metadata
- Defining and staying inside scope

## AI acceleration
A model will synthesise scattered recon output into a tidy attack-surface map fast — and
just as fast hallucinate a subdomain that doesn't resolve. Treat its output as leads to
verify, never as confirmed assets, and never let it talk you out of scope.
