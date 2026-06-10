# Module 09 — Email Authentication

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *SPF, DKIM, and DMARC are the three DNS records that determine whether a domain can be spoofed for phishing — and most organisations have at least one wrong.*

## Why this matters

Email spoofing is the enabler of phishing and business email compromise (BEC) — the most financially damaging cybercrime category. SPF, DKIM, and DMARC are the three DNS-based standards that, when correctly configured, tell receiving mail servers whether a message claiming to be from your domain actually came from an authorised source. Without them, an attacker can send email that appears to come from `cfo@meridian.com` with no technical barrier. With all three correctly configured, spoofed email is either rejected or marked as spam before reaching the target's inbox. This is not a complex or expensive control — it is three DNS records — and its absence is a compliance finding in every email security audit.

## Objective

Configure and validate SPF, DKIM, and DMARC records for a fictional domain using a local DNS environment, understanding what each record does, what failure mode each prevents, and how DMARC brings them together into a policy.

## The core idea

SPF (Sender Policy Framework) authorises which IP addresses or servers are allowed to send email on behalf of a domain. The receiving mail server checks whether the sending IP appears in the domain's SPF record; if not, the check fails. SPF alone does not prevent spoofing in the visible "From" header — it checks the envelope sender (the SMTP `MAIL FROM` command), which is not typically shown to users. A domain with a strong SPF record and no DMARC can still be spoofed in the visible From address (the "header from"), which is the address the user actually sees.

DKIM (DomainKeys Identified Mail) adds a cryptographic signature to the message. The signing server generates an RSA or Ed25519 signature over selected headers (including the From address) and the message body, and includes it in a `DKIM-Signature` header. The receiving server fetches the public key from the sender's DNS (a TXT record at `selector._domainkey.domain.com`) and verifies the signature. A valid DKIM signature proves that the message content and the From header were not modified in transit and were signed by a party controlling the domain's private key. DKIM survives email forwarding (where SPF breaks because the forwarding server's IP is not in the SPF record).

DMARC (Domain-based Message Authentication, Reporting and Conformance) is the policy layer that ties SPF and DKIM together and adds alignment and reporting. A DMARC record specifies what to do if a message fails both SPF and DKIM: `none` (monitor only), `quarantine` (spam folder), or `reject` (bounce). It also specifies alignment: the domain in the SPF check or the DKIM signature must match the domain in the visible From header (`d=` alignment). This is the alignment requirement that closes the gap SPF alone leaves — a DMARC `reject` policy with DKIM alignment prevents spoofing the visible From address even if the attacker passes the envelope SPF check. DMARC also enables aggregate (`rua`) and forensic (`ruf`) reporting — receiving servers send reports back to the domain owner showing which sources are passing and failing authentication, which is how you audit your own email sending infrastructure before setting a `reject` policy.

The operational pattern for DMARC deployment is a staged rollout: start with `p=none` (monitor), collect reports for 30–60 days to ensure all legitimate sending infrastructure passes SPF and DKIM, then move to `p=quarantine`, then to `p=reject`. Jumping to `reject` without a monitoring period routinely causes legitimate email to be bounced — newsletters, third-party SaaS sending on behalf of the domain, and marketing platforms all need to be authorised in SPF and DKIM-signed before `reject` is safe.

## Learn (~3 hrs)

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

## AI acceleration

Ask an AI to write the SPF, DKIM, and DMARC TXT records for a fictional domain with two authorised sending IPs. Then validate the records against the RFC syntax: is the SPF record a valid `v=spf1` record? Does the DMARC record include `v=DMARC1`? Does the DKIM record have a valid `p=` (public key)? Use [MXToolbox](https://mxtoolbox.com/SuperTool.aspx) to validate any records for a real domain you control.
