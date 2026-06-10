# Module 06 — Identity-Aware Access

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *every request carries proof of who you are before a packet reaches your service.*

## Why this matters

Traditional network access draws a hard line at the perimeter: once inside the VPN or office LAN, you are trusted implicitly and can reach most internal services. This assumption collapsed under hybrid work, cloud adoption, and the steady drumbeat of lateral-movement-after-VPN-compromise incidents. Identity-aware access replaces the binary inside/outside question with a per-request question: who is asking, what are they asking for, and does policy allow it — right now, for this specific resource?

The practical consequence is that your internal services can stop listening on the public internet entirely. An identity-aware proxy sits in front of them, terminates inbound TLS, validates the caller's identity token, enforces policy, and only then forwards the request upstream. No valid token, no connection — not a 401, not a login page, a dropped packet. Attackers scanning your IP range see nothing to attack.

## Objective

Stand up Pomerium as an identity-aware proxy in front of a backend service, observe what happens to an unauthenticated request, then trace an authenticated request through the proxy to prove the header and policy chain work end-to-end.

## The core idea

The mental model that cuts through the marketing is simple: an identity-aware proxy is a **reverse proxy that speaks OIDC**. Instead of a firewall rule that allows TCP/443, you have a process that requires a signed JWT (issued by your IdP) in every request. The proxy validates the token's signature, expiry, and claims against a policy, then either proxies the request or rejects it. The backend service has no knowledge of this — it just sees HTTP requests that arrive with user-identity headers injected by the proxy.

What makes Pomerium interesting in the OSS landscape is that it bundles the three components you otherwise have to wire together manually: an **authentication service** (handles OIDC redirects with your IdP), a **authorization service** (evaluates policy against identity claims), and a **proxy service** (actually forwards the traffic). In the lab you run all three in a single container for simplicity; production deployments split them for scale and blast-radius reasons.

The claim-to-policy mapping is where practitioners get burned. A policy that says `allow if email ends in @meridian.com` sounds reasonable until you realize your IdP also issues tokens to contractors with `@meridian-partner.com` addresses, or that email-only claims don't capture the difference between a finance analyst and a junior developer. Real ZT policy matches on groups or roles that the IdP manages, not on email strings — because the IdP is the system of record for that identity, and it enforces MFA and device posture before issuing the token. The proxy is the enforcement point; the IdP is the authority.

One architectural gotcha: Pomerium (and every similar proxy) terminates TLS inbound, which means your backend service sees internal HTTP from the proxy, not HTTPS from the end user. The original client IP, the user's identity, and the validated claims arrive as injected request headers (`X-Pomerium-Jwt-Assertion`, `X-Forwarded-For`). Your backend must trust only those headers from the proxy and strip any attempt by a caller to forge them — never forward user-injected identity headers to a backend that reads them without validation.

Tailscale takes a different approach: rather than an inbound proxy, it gives each device and service a WireGuard tunnel identity, so network-level access itself becomes identity-bound. The same "no open ports" outcome, but at the network layer rather than the application layer. Both patterns matter; which you reach for depends on whether you control the application (proxy is easier) or the infrastructure (Tailscale is simpler for ops).

## Learn (~3 hrs)

**Zero Trust fundamentals (~45 min)**
- [NIST SP 800-207 — Zero Trust Architecture, §2–3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf) — the authoritative definition; skim §2 for tenets and §3 for deployment models. Everything else in this module maps back here.
- [BeyondCorp: A New Approach to Enterprise Security (Google, 2014)](https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/) — the paper that made "ditch the VPN" credible. Short read; focus on the access proxy and the device inventory components.

**Identity-aware proxies in practice (~1 hr)**
- [How Pomerium works — architecture overview](https://www.pomerium.com/docs/internals/architecture) — the data-flow diagram is the fastest way to see where JWT validation sits relative to upstream forwarding.

**OIDC and JWT without the hand-waving (~45 min)**
- [An Illustrated Guide to OAuth and OpenID Connect (Okta Developer Blog)](https://developer.okta.com/blog/2019/10/21/illustrated-guide-to-oauth-and-oidc) — the flow diagrams make the token handshake concrete; this is the "raw explanation" that the core-idea section above assumes you've read.

**Tailscale and network-layer ZT (~30 min)**
- [Tailscale: How it works](https://tailscale.com/blog/how-tailscale-works) — explains WireGuard mesh, DERP relays, and ACLs in plain English; useful contrast to the proxy model.

## Key concepts
- An identity-aware proxy requires a valid IdP-issued token on every request — not once per session.
- The proxy terminates TLS; the backend sees injected identity headers, not the original token.
- Policy should be bound to IdP-managed groups/roles, not raw email strings.
- Pomerium bundles authenticate + authorize + proxy; production splits these for scale.
- Tailscale is network-layer ZT; Pomerium is application-layer ZT — pick based on control-plane access.
- "No open ports" is the outcome: the backend service never listens on a public address.

## AI acceleration

AI is useful for generating Pomerium policy blocks — paste your IdP's JWT claim structure and ask it to write the `allow` and `deny` stanzas. The thing you must verify manually: **test the deny path**, not just the allow path. AI-generated policy tends to be too permissive. Run a request with a token that should be denied and confirm you get a 403 or a redirect to a blocked page, not a 200. Also confirm that the backend cannot be reached by bypassing the proxy (no direct port exposure).
