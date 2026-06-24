# Module 09 — Email Authentication

*Type 2 · Misconception Reveal — you predict SPF stops spoofing, then see it never checks the visible From; DMARC alignment closes the gap, staged none→quarantine→reject. (Secondary: Audit→Build→Verify.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**[Track 08 — Cryptography, PKI & Secrets]** — *SPF, DKIM, and DMARC are the three DNS records that determine whether a domain can be spoofed for phishing — and most organisations have at least one wrong.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

Between 2013 and 2015, a Lithuanian man named Evaldas Rimasauskas tricked **Google and Facebook into wiring over $100 million** to his accounts — by registering a company with the same name as a hardware supplier the two firms actually paid, then emailing convincing fake invoices to their finance teams ([U.S. DOJ, SDNY — "Lithuanian Man Pleads Guilty To Wire Fraud For Theft Of Over $100 Million In Fraudulent Business Email Compromise Scheme"](https://www.justice.gov/usao-sdny/pr/lithuanian-man-pleads-guilty-wire-fraud-theft-over-100-million-fraudulent-business)). The technical enabler of that whole category is that email, by default, lets anyone claim to be anyone — there is no built-in check that a message from "your supplier" actually came from your supplier's domain. Email spoofing is the enabler of phishing and business email compromise (BEC) — the most financially damaging cybercrime category. SPF, DKIM, and DMARC are the three DNS-based standards that, when correctly configured, tell receiving mail servers whether a message claiming to be from your domain actually came from an authorised source. Without them, an attacker can send email that appears to come from `cfo@corp-fictional.com` with no technical barrier. With all three correctly configured, spoofed email is either rejected or marked as spam before reaching the target's inbox. This is not a complex or expensive control — it is three DNS records — and its absence is a compliance finding in every email security audit.

## Objective

Configure and validate SPF, DKIM, and DMARC records for a fictional domain using a local DNS environment, understanding what each record does, what failure mode each prevents, and how DMARC brings them together into a policy — then *apply* the fix: edit the live DNS zone to the hardened records (`-all`, `p=reject`, `adkim=s`, `rua=`), reload the resolver, and **prove** with a re-query and a re-run of your validation script that the weaknesses are gone. Finding the misconfiguration and closing it on the live zone are equal halves.

## The core idea

SPF (Sender Policy Framework) authorises which IP addresses or servers are allowed to send email on behalf of a domain. The receiving mail server checks whether the sending IP appears in the domain's SPF record; if not, the check fails. SPF alone does not prevent spoofing in the visible "From" header — it checks the envelope sender (the SMTP `MAIL FROM` command), which is not typically shown to users. A domain with a strong SPF record and no DMARC can still be spoofed in the visible From address (the "header from"), which is the address the user actually sees.

DKIM (DomainKeys Identified Mail) adds a cryptographic signature to the message. The signing server generates an RSA or Ed25519 signature over selected headers (including the From address) and the message body, and includes it in a `DKIM-Signature` header. The receiving server fetches the public key from the sender's DNS (a TXT record at `selector._domainkey.domain.com`) and verifies the signature. A valid DKIM signature proves that the message content and the From header were not modified in transit and were signed by a party controlling the domain's private key. DKIM survives email forwarding (where SPF breaks because the forwarding server's IP is not in the SPF record).

DMARC (Domain-based Message Authentication, Reporting and Conformance) is the policy layer that ties SPF and DKIM together and adds alignment and reporting. A DMARC record specifies what to do if a message fails both SPF and DKIM: `none` (monitor only), `quarantine` (spam folder), or `reject` (bounce). It also specifies alignment: the domain in the SPF check or the DKIM signature must match the domain in the visible From header (`d=` alignment). This is the alignment requirement that closes the gap SPF alone leaves — a DMARC `reject` policy with DKIM alignment prevents spoofing the visible From address even if the attacker passes the envelope SPF check. It is precisely this "is the From domain who it claims to be?" check that was missing in the Google/Facebook BEC fraud, where look-alike sender domains carried fake invoices straight to finance. DMARC also enables aggregate (`rua`) and forensic (`ruf`) reporting — receiving servers send reports back to the domain owner showing which sources are passing and failing authentication, which is how you audit your own email sending infrastructure before setting a `reject` policy.

The operational pattern for DMARC deployment is a staged rollout: start with `p=none` (monitor), collect reports for 30–60 days to ensure all legitimate sending infrastructure passes SPF and DKIM, then move to `p=quarantine`, then to `p=reject`. Jumping to `reject` without a monitoring period routinely causes legitimate email to be bounced — newsletters, third-party SaaS sending on behalf of the domain, and marketing platforms all need to be authorised in SPF and DKIM-signed before `reject` is safe.

## Learn (~3 hrs)

**Email spoofing's real-world failure — the *why* (~10 min)**
- [U.S. DOJ (SDNY) — "Lithuanian Man Pleads Guilty To Wire Fraud … Over $100 Million … Business Email Compromise Scheme"](https://www.justice.gov/usao-sdny/pr/lithuanian-man-pleads-guilty-wire-fraud-theft-over-100-million-fraudulent-business) — the Evaldas Rimasauskas case: look-alike sender domains and fake invoices induced Google and Facebook to wire over $100M (2013–2015). The primary-source proof that "anyone can claim to be anyone" in email is a real, nine-figure problem — and why sender authentication exists.

**SPF, DKIM, and DMARC — the standards**
- [RFC 7208 — SPF (Sender Policy Framework)](https://www.rfc-editor.org/rfc/rfc7208) — Sections 1–5 for the mechanism and terminology; the normative reference.
- [RFC 6376 — DKIM Signatures](https://www.rfc-editor.org/rfc/rfc6376) — Sections 1–4 for the signing model and verification process.
- [RFC 7489 — DMARC](https://www.rfc-editor.org/rfc/rfc7489) — Sections 1–7 for the policy model, alignment, and reporting.

**Practical deployment**
- [MXToolbox SPF/DKIM/DMARC guides](https://mxtoolbox.com/dmarc/details/what-is-a-dmarc-record) — practical explanations with examples; read the SPF, DKIM, and DMARC entries for a practitioner's view of each record format.
- [Google's DMARC deployment guide](https://support.google.com/a/answer/2466580) — the staged `none` → `quarantine` → `reject` rollout; a clear operational guide.

**Testing tools**
- [mail-tester.com](https://www.mail-tester.com/) — real-world SPF/DKIM/DMARC test for a domain you control.

## Key concepts

- SPF authorises sending IPs via a DNS TXT record; checks the envelope sender (not the visible From).
- DKIM adds a cryptographic signature over the From header and body; public key in DNS.
- DMARC ties SPF and DKIM together with alignment checking and sets the policy: none / quarantine / reject.
- Alignment: the domain in SPF/DKIM must match the visible From domain — this is what prevents From-header spoofing.
- DMARC rollout: `none` (monitor) → `quarantine` → `reject`; never skip the monitoring phase.
- The **Google/Facebook BEC** ($100M+, Evaldas Rimasauskas, 2013–2015) is the canonical proof that unauthenticated sender identity is a nine-figure business risk, not a compliance checkbox.
- Author then verify: apply the hardened records to the live zone, reload, and prove with `dig` + your validator that SPF hardfails and DMARC rejects — the build half, not just a recommendation in a report.

## AI acceleration

Ask an AI to write the SPF, DKIM, and DMARC TXT records for a fictional domain with two authorised sending IPs. Then validate the records against the RFC syntax: is the SPF record a valid `v=spf1` record? Does the DMARC record include `v=DMARC1`? Does the DKIM record have a valid `p=` (public key)? Use [MXToolbox](https://mxtoolbox.com/SuperTool.aspx) to validate any records for a real domain you control.
