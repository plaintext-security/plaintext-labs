# Module 11 — Red-team Your Zero-Trust Deployment

*Type 10 · Design → red-team-your-own-design → harden — you have already built the gated service (Modules 05/06); here you **attack your own design**, then harden the one finding that holds, then re-attack until it fails too. The deliverable is the attacks that *failed* (the design held, documented) plus the one that didn't, hardened. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *a control you haven't attacked is a hope, not a control.*

<!-- module-meta -->
**Difficulty:** Intermediate–Advanced &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md); Module 05 (SASE / no-inbound-ports) and Module 06 (Identity-Aware Access / Pomerium) — you red-team the deployment you stood up there
{ .module-meta }

## Why this matters

There is a gap between "I deployed Zero Trust" and "I proved it holds," and most deployments live in it. A `docker compose up` that returns a green dashboard, a tunnel that shows *connected*, an Access policy that asks for an email — these tell you the happy path works. They tell you nothing about whether the design refuses the attacks it was built to refuse. You only trust a control after you have attacked it yourself and watched it hold; until then it is an assertion.

This is not theoretical caution. The header-trust failure class is one of the most common ways a real Zero-Trust proxy quietly becomes theater. In **CVE-2026-40575** (OAuth2 Proxy, CVSS 9.1, fixed in 7.15.2), an unauthenticated attacker could spoof the `X-Forwarded-Uri` header so the proxy evaluated its auth and skip-auth rules against a *different* path than the one actually forwarded upstream — reaching protected routes with no session at all. The fix was a `--trusted-proxy-ip` allowlist: stop trusting `X-Forwarded-*` headers from anyone but the real upstream proxy. The lesson generalizes far past one CVE: any forward-auth design that trusts a client-settable header, or that leaves the backend reachable *around* the proxy, has a deny path that was never actually tested. Red-teaming your own deployment is how you find that out before an attacker does — and the artifact you walk away with (the four attacks, three of which failed by design and one you hardened) is exactly the evidence a security review or an auditor asks for.

## Objective

Take the gated, no-inbound-ports service you built in Modules 05/06 and attack it as an outsider would: prove nothing listens (external port scan), prove an unauthenticated request is denied, attempt to forge the proxy's identity headers to impersonate a user, and attempt to bypass the proxy straight to the backend. Document the attacks that *failed* (the design held) as evidence; for the one that succeeds against a deliberately naive backend, harden it and re-attack until it fails too.

## The core idea

The deliverable is the design plus the attacks it survived — so the structure of this module is four attacks, each targeting one tenet of the architecture you built, and each producing a documented pass (it was refused) or fail (it got through, and now you harden). The mental model is one sentence: **a control you haven't attacked is a hope, not a control.** Deployment proves the happy path; red-teaming proves the deny path, and the deny path is the only thing that makes it Zero Trust.

The four attacks map one-to-one onto the design's load-bearing tenets. **(1) No inbound listener** — an external port scan (`nmap` against the host/origin) must find nothing; the connector dialed *out* (Cloudflare Tunnel) or the backend has no published port (Pomerium), so there is no service to reach and nothing to fingerprint. **(2) No unauthenticated reach** — an `https` request with no session must land on a login/redirect or a drop, never a 200 from the backend. These two are the easy passes; if either fails, the deployment isn't Zero Trust yet and the later attacks are moot.

The third attack is the one this module exists for: **identity-header forgery.** An identity-aware proxy works by *injecting* the validated caller into the upstream request as a header — Pomerium's signed `X-Pomerium-Jwt-Assertion`, plus context like `X-Forwarded-For` / `X-Forwarded-User`. The whole model holds right up until the backend trusts a header that an attacker can *also* set. `curl -H "X-Forwarded-User: admin@corp.com"` costs nothing; a forged value of a *signed* assertion costs the proxy's private key, which you don't have. So the rule the backend must follow is exact: **trust the identity in `X-Pomerium-Jwt-Assertion` only after verifying its signature against the proxy's JWKS (`/.well-known/pomerium/jwks.json`), plus `aud`/`iss`/`exp` — and never trust a plain, client-supplied identity header.** The lab ships *two* backends so you can see both sides: a properly-verifying one (the forgery is refused — a documented pass) and a deliberately naive one that believes a raw `X-Forwarded-User` header (the forgery *succeeds* — your one finding). Hardening the naive backend to verify the signed assertion, then watching the same forgery fail, is the harden-and-re-attack beat that *is* the deliverable.

The fourth attack is the dual of the first: **proxy bypass.** Even a perfect deny path is decoration if the backend is reachable without traversing it — a published port "for convenience," a route on a flat internal network, a teammate's `docker run -p`. Try to reach the backend directly; it must refuse. The honest framing throughout: each attack is run *against your own deployment only*, and a refusal is a documented win — "I attacked this and it held" — not a non-event. The one finding you do land is not a failure of the exercise; it is the exercise working. A red-team that finds nothing on the first pass either has a hardened design or a shallow attack — and the way you tell the difference is by including a known-vulnerable backend and confirming your attack can actually detect the difference.

## Learn (~2.5 hrs)

**The design you're attacking — what each tenet promises (~45 min)**
- [NIST SP 800-207 — Zero Trust Architecture, §2 (tenets) and §3.4 (threats to ZTA)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf) (~30 min) — §2 is the checklist your four attacks test; **read §3.4 closely** — it enumerates exactly the deployment-level threats (subverting the policy decision/enforcement point, denial-of-service of the PEP, stolen credentials) that this red-team operationalizes. The PDP/PEP split there is the proxy-vs-backend boundary you attack.
- [Pomerium — JWT verification ("Continuous Identity Verification at the Application Layer")](https://www.pomerium.com/docs/guides/jwt-verification) (~15 min) — the centerpiece reference: what the *backend* must check on `X-Pomerium-Jwt-Assertion` (signature against the JWKS, `aud`/`iss`/`exp`) before trusting any claim. This is the rule the naive backend violates and the verifying backend obeys.

**The header-trust failure class, made real (~40 min)**
- [OAuth2 Proxy — "Authentication Bypass via X-Forwarded-Uri Header Spoofing" (CVE-2026-40575, GHSA-7x63-xv5r-3p2x)](https://github.com/oauth2-proxy/oauth2-proxy/security/advisories/GHSA-7x63-xv5r-3p2x) (~15 min) — the recent, real, CVSS-9.1 advisory the forgery attack is built around. Read the affected-config conditions and the fix (the `--trusted-proxy-ip` allowlist) — that allowlist *is* the lesson: trust `X-Forwarded-*` only from the real proxy.
- [Pomerium — X-Forwarded-For Settings (`xff_num_trusted_hops`)](https://www.pomerium.com/docs/reference/x-forwarded-for-settings) (~10 min) — Pomerium's own knob for the same problem: when `xff_num_trusted_hops` is 0/unset, the incoming `X-Forwarded-For` is *not* trusted. Read it as the concrete "how a real product refuses a spoofed header" counterpart to the CVE.
- [adam-p — "The perils of the 'real' client IP" (X-Forwarded-For)](https://adam-p.ca/blog/2022/03/x-forwarded-for/) (~15 min) — the clearest practitioner writeup of *why* any client-settable header is untrustworthy unless added by a proxy you control. Read the "spoofing" and "which hop do I trust?" sections; it generalizes the CVE to the whole class.

**The attack tooling (~25 min, skim — you've met these in Foundations)**
- [Nmap — Host Discovery and Port Scanning Basics (official reference guide)](https://nmap.org/book/man-host-discovery.html) (~15 min) — you need only the basic TCP connect/SYN scan and the "no open ports" reading; this is the "prove nothing listens" tool. Skip the scripting-engine chapters.
- [PortSwigger Web Security Academy — HTTP request smuggling / header notes](https://portswigger.net/web-security/request-smuggling) (~10 min, optional) — read only as background on why proxies and backends disagreeing about a request is a recurring bug class; the header-forgery you run is the simplest member of that family.

## Key concepts
- **A control you haven't attacked is a hope, not a control.** Deployment proves the happy path; only red-teaming proves the deny path — and the deny path is what makes it Zero Trust.
- The four attacks map to four tenets: **(1)** no inbound listener (port scan finds nothing), **(2)** no unauthenticated reach (no-session request is denied), **(3)** no forged identity (a client-set identity header is rejected/overwritten), **(4)** no proxy bypass (the backend is unreachable except through the proxy).
- **Header trust is the gotcha.** The backend must trust only the proxy's *signed* assertion (`X-Pomerium-Jwt-Assertion`), verified against the JWKS + `aud`/`iss`/`exp` — never a plain, client-supplied header. Forging an unsigned header is free; forging a signed one needs the proxy's private key. CVE-2026-40575 is this exact class.
- **Bypass is the dual of denial.** Every path to the backend must pass through the proxy; a published port or flat-network route makes the entire deny path moot.
- **A refused attack is a documented win**, not a non-event — "I attacked this and it held" is the artifact. The one finding you *do* land is the exercise working; you harden it and re-attack until it fails too.
- A red-team that finds nothing on its first pass may have a hardened design *or* a shallow attack — include a known-vulnerable backend so you can confirm your attack actually distinguishes the two.

## AI acceleration

A model will happily draft your whole attack harness — the `nmap` invocation, the four `curl` probes, the forged-header payloads — in one shot, and that speed is genuinely useful here. The posture holds exactly as everywhere else: **AI authors → you review every line → you own it**, and in a red-team harness the review has one specific failure mode to hunt. An attack script that **fails open** — that prints PASS when the request errors, times out, or hits a redirect the script didn't anticipate — will tell you your design held when in fact your *test* broke. Every assertion must fail *closed*: a probe that can't reach a verdict counts as a failure to investigate, never a silent pass. Make a model draft `attack.sh`, then read each check and ask: if this `curl` returned nothing, or a 000, or an unexpected 502, does the harness report a held design or a broken test? The transferable skill of this module is not prompting for `nmap` flags; it's owning a red-team harness whose green you can actually trust — and proving it by pointing the *same* harness at the deliberately-naive backend and watching it correctly go red.
