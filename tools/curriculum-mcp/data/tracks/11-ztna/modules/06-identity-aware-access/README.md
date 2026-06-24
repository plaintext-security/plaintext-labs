# Module 06 — Identity-Aware Access

*Type 7 · Build-&-Operate — stand up an identity-aware proxy and run it; the deliverable is the operating proxy and its verified deny path, not an essay. (Secondary: Judgment-as-Code — the regression test that proves the deny path can't silently open.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *every request carries proof of who you are before a packet reaches your service.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md), and Module 02 (Identity as the Control Plane) for OIDC/JWT
{ .module-meta }

## Why this matters

Traditional network access draws a hard line at the perimeter: once inside the VPN or office LAN, you are trusted implicitly and can reach most internal services. That assumption collapsed under hybrid work, cloud adoption, and a decade of lateral-movement-after-VPN-compromise incidents. Identity-aware access replaces the binary inside/outside question with a per-request one: who is asking, what are they asking for, and does policy allow it — right now, for this specific resource? The practical payoff is that your internal services stop listening on the public internet entirely. A proxy sits in front, terminates inbound TLS, validates the caller's identity token, enforces policy, and only then forwards upstream. No valid token, no connection — not a 401, not a login page, a dropped packet. Attackers scanning your IP range see nothing.

But the proxy only buys you that protection if the **backend trusts only the proxy** — and that is exactly where real deployments fail. An identity-aware proxy works by *injecting* the validated identity into the upstream request as headers. The whole model is sound until a header an attacker can also set is trusted as if the proxy set it. In **CVE-2026-40575** (OAuth2 Proxy, CVSS 9.1), a client could spoof the `X-Forwarded-Uri` header so the proxy evaluated its auth and skip-auth rules against a *different* path than the one actually forwarded to the app — an unauthenticated attacker reaching protected routes. The same failure class shows up wherever a forward-auth proxy trusts a client-settable `X-Forwarded-User` / `X-Forwarded-Uri` header, or wherever the backend is reachable *around* the proxy (a published port, a flat internal network) so a request never passes the identity check at all. The proxy is only as strong as the backend's refusal to trust anything but the proxy's signed proof.

## Objective

Stand up Pomerium as an identity-aware proxy in front of a backend service; observe a packet-level denial of an unauthenticated request; trace an authenticated request end-to-end and read the injected identity headers; then prove the two ways this architecture is forged — a client-supplied identity header, and a direct-to-backend bypass — and confirm your deployment refuses both.

## The core idea

An identity-aware proxy is, stripped of marketing, a **reverse proxy that speaks OIDC**. Instead of a firewall rule that allows TCP/443, you have a process that requires a signed JWT (issued by your IdP) on every request, validates its signature, expiry, and claims against a policy, then either forwards the request or rejects it. The backend has no knowledge of any of this — it just sees HTTP arriving with user-identity headers the proxy injected. Pomerium bundles the three pieces you would otherwise wire by hand: an **authenticate** service (the OIDC redirect dance with your IdP), an **authorize** service (policy evaluation against claims), and a **proxy** (the actual forwarding). The lab runs all three in one container for legibility; production splits them for scale and blast radius.

**The load-bearing judgment of this module is the deny path, and the gotcha that defeats it is header trust.** The proxy terminates TLS inbound, so the backend sees internal HTTP from the proxy, not HTTPS from the user. Identity arrives as injected headers — the signed `X-Pomerium-Jwt-Assertion` (a JWT the proxy signs with its own key) plus context like `X-Forwarded-For`. The mistake that turns a Zero-Trust deployment into theater: **the backend must trust *only* the proxy's signed assertion, never a client-supplied identity header.** Headers are trivially forgeable — `curl -H "X-Forwarded-User: admin@corp.com"` costs nothing — so a backend that reads an *unsigned* identity header and believes it has handed authentication to the attacker. Pomerium's own guidance is explicit: the upstream verifies the assertion cryptographically — the JWT was signed by Pomerium's key (fetched from the `/.well-known/pomerium/jwks.json` JWKS endpoint), the `aud`/`iss` match the service, and `exp` is in the future — *before* trusting any identity inside it. A signed assertion is unforgeable without the proxy's private key; a plain header is not. That distinction is the entire security boundary.

The second way the deny path fails is **bypass**: if the backend is reachable around the proxy — a published port, a route on a flat internal network, a teammate who `docker run`s it with `-p` for convenience — then no request ever hits the identity check and the proxy is decoration. "No open ports" is not a nice-to-have; it is the precondition that makes the proxy's verdict the *only* way in. The two failures are duals of the same rule: every path to the backend must pass through the proxy (no bypass), and the backend must believe only what the proxy cryptographically signs (no forged header).

A note on policy, because it is the third place practitioners get burned: a policy that says `allow if email ends in @corp.com` sounds reasonable until the IdP also issues tokens to `@corp-partner.com` contractors, or until you need to distinguish a finance analyst from a junior dev. Real ZT policy matches on **IdP-managed groups or roles**, not raw email strings — the IdP is the system of record (it enforces MFA and device posture before issuing the token); the proxy is only the enforcement point. (Tailscale reaches the same "no open ports" outcome at the *network* layer — each device gets a WireGuard tunnel identity — rather than the application layer; which you pick depends on whether you control the app, where a proxy is easier, or the infrastructure, where the mesh is.)

## Learn (~3 hrs)

**Zero Trust fundamentals (~45 min)**
- [NIST SP 800-207 — Zero Trust Architecture, §2–3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf) (~25 min) — the authoritative definition; read §2 for the tenets and §3 for deployment models. The "policy enforcement point vs policy decision point" split in §3 is exactly the authorize-vs-proxy division you stand up in the lab.
- [BeyondCorp: A New Approach to Enterprise Security (Google, 2014)](https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/) (~20 min) — the paper that made "ditch the VPN" credible. Focus on the access proxy and device-inventory components; skip the rollout sections.

**The proxy architecture and where validation sits (~1 hr)**
- [How Pomerium works — architecture overview](https://www.pomerium.com/docs/internals/architecture) (~20 min) — the data-flow diagram is the fastest way to see where JWT validation sits relative to upstream forwarding. Note which component injects the assertion header.
- [Pomerium — JWT verification ("Continuous Identity Verification at the Application Layer")](https://www.pomerium.com/docs/guides/jwt-verification) (~25 min) — **read this one closely; it is the centerpiece of the module.** It spells out exactly what the *backend* must check on `X-Pomerium-Jwt-Assertion` (signature against the JWKS, `aud`/`iss`, `exp`) before trusting any claim — i.e. why a signed assertion is safe and a plain header is not.

**OIDC and JWT without the hand-waving (~45 min)**
- [An Illustrated Guide to OAuth and OpenID Connect (Okta Developer Blog)](https://developer.okta.com/blog/2019/10/21/illustrated-guide-to-oauth-and-oidc) (~30 min) — the flow diagrams make the token handshake concrete; this is the "raw explanation" the core-idea section assumes. (Module 02 already had you mint and validate a JWT — this is the refresher if the claim/signature mechanics are hazy.)
- [OAuth2 Proxy — `X-Forwarded-Uri` header-spoofing advisory (CVE-2026-40575)](https://github.com/oauth2-proxy/oauth2-proxy/security/advisories/GHSA-7x63-xv5r-3p2x) (~10 min) — the real, recent (CVSS 9.1) incident the header-trust gotcha is built around. Read the "specific conditions" and the fix (the `--trusted-proxy-ip` allowlist) — that *is* the lesson, made into a CVE.

## Key concepts
- An identity-aware proxy requires a valid IdP-issued token on **every request** — not once per session — and only then forwards to a backend that never listens publicly.
- The proxy terminates TLS; the backend sees injected identity headers, not the original token.
- **The backend must trust only the proxy's *signed* assertion (`X-Pomerium-Jwt-Assertion`), verified against the JWKS — never a plain, client-supplied identity header.** Forging an unsigned header is free; forging a signed one needs the proxy's private key.
- **No bypass:** every path to the backend must pass through the proxy. A published port or flat-network route around it makes the whole deny path moot. Header-forgery and bypass are the two duals of the same rule.
- Policy should bind to IdP-managed groups/roles, not raw email strings; the IdP is the authority, the proxy is the enforcement point.
- Pomerium bundles authenticate + authorize + proxy (production splits them); Tailscale is the network-layer alternative to this application-layer pattern.

## AI acceleration

A model will draft a Pomerium `policy` block in seconds — paste your IdP's claim structure and ask for the `allow`/`deny` stanzas — and that speed is exactly the risk: **AI-generated access policy skews permissive**, and the only way to know is to send a request that *should* fail. The posture holds — AI authors → you review every line → you own it — and here it has a concrete shape: never accept the policy on the allow path alone. Test the **deny path** yourself (a token that should be rejected, a forged identity header, a direct-to-backend request) and confirm each is refused, not a 200. That review is exactly what the lab's required `check-deny.sh` regression test makes permanent: the secondary Judgment-as-Code beat of this module is encoding your verdict ("the unauthenticated and the forged-header paths stay closed") as a script so a future config change can't silently reopen them.
