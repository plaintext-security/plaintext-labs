# Module 07 — Web Attacks: Authentication & Access Control

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *broken access control is OWASP's #1 risk for a reason.*

## Why this matters
Most web apps get the flashy bugs right and the boring ones wrong: weak authentication,
broken session handling, and — above all — broken access control, where you simply ask for
data that isn't yours and the server hands it over. It tops the OWASP Top 10 because it's
everywhere and trivially exploited. Finding it is mostly discipline, not cleverness.

## Objective
Identify and exploit authentication and access-control flaws — including IDOR and privilege
escalation — and explain the fix.

## The core idea
Authentication is "who are you"; **authorization** is "what are you allowed to do" — and broken access
control (the authorization failure) tops the OWASP Top 10 because it's everywhere and trivially
exploited. The mechanism is almost embarrassing: most apps enforce access at the *UI* (hide the button)
but not at the *API* (the server still answers if you ask directly). So the attack is just *asking* —
change `id=123` to `124` and read someone else's record (IDOR), call the admin endpoint as a normal
user (vertical escalation), or reach a peer's data (horizontal). No payload, no cleverness.

Seen through the lens of the injection module, this is the same disease in a new organ: **the server
trusting the client.** Injection is the server trusting client *input*; broken access control is the
server trusting the client to *only ask for what it should*. Both fixes are therefore structural and
identical in spirit — never trust the client: enforce authorization server-side, deny-by-default, on
*every* request, not by hiding options the user can still call.

The judgment: this finding is won by **discipline, not brilliance.** You check every action as every
role — admin, normal user, other user, no auth — and diff what comes back. It's tedious, which is
exactly why it's the #1 risk: the boring enumeration gets skipped by developers and testers alike. A
model helps brainstorm which IDs or roles to try, but it won't methodically walk every endpoint × every
role for you — that disciplined sweep is the job.

## Learn (~4 hrs)

**Hands-on labs**
- [PortSwigger — Authentication vulnerabilities](https://portswigger.net/web-security/authentication) — credential, session, and MFA flaws, with labs.
- [PortSwigger — Access control & IDOR](https://portswigger.net/web-security/access-control) — the highest-value, most common class.

**Reference**
- [OWASP Top 10 — A01: Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/) — why it's ranked #1, with real examples.

## Key concepts
- Authentication vs authorization (the distinction that matters here)
- Insecure Direct Object References (IDOR)
- Vertical vs horizontal privilege escalation
- Session handling and token flaws
- The fix: enforce access control server-side, deny by default

## AI acceleration
A model helps you reason about which object IDs or roles to try — but access-control testing
is about methodically checking *every* action as *every* role, which a model won't do for
you. Use it to brainstorm; you do the disciplined enumeration.
