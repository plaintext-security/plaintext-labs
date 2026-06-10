# Module 04 — ZTNA Architectures

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *four patterns, one principle: match the architecture to the threat model, not to the vendor's marketing.*

## Why this matters

"Zero Trust" is now a requirement in government mandates (the 2021 Biden Executive Order), a sales
term applied to products that have little to do with ZT principles, and a genuine architectural
shift that organizations are in various stages of implementing. The practitioner skill is being able
to look at a specific organization's access patterns and say: which of the four ZT delivery
patterns fits best, what are the operational trade-offs, and where is the blast-radius boundary if
this pattern is compromised? That skill requires understanding the patterns independently of any
single vendor.

## Objective

Read the structured comparison of four ZTNA patterns, map Meridian Financial's requirements and
constraints against each pattern, and produce an Architecture Decision Record (ADR) that recommends
a pattern with a clear rationale a security architect could defend to a CISO.

## The core idea

There is no single ZTNA architecture. The ZT principle is consistent — never trust, always verify,
enforce least-privilege access at the resource — but the delivery mechanism varies substantially
depending on where applications live, who is accessing them, what device posture signals are
available, and how much operational complexity the team can sustain. Practitioners who confuse "we
bought a ZTNA product" with "we have Zero Trust" are usually in the position of having deployed one
pattern without understanding why it was chosen or what threat model it addresses.

The four patterns worth understanding are: **VPN** (the baseline to improve on), **reverse proxy**
(an application-layer broker like Pomerium), **network mesh** (WireGuard-based peer-to-peer like
Tailscale/headscale), and **cloud edge** (globally distributed enforcement like Cloudflare Zero
Trust). Each of these sits at a different layer of the stack and makes a different trade-off.

A **VPN** enforces access at the network perimeter: authenticate once, get a virtual IP, and
communicate freely with anything in the network. The trade-off is blast radius: a single
compromised credential (with no continuous re-evaluation) grants full network access. VPNs are
not inherently "un-Zero Trust" — a well-configured, micro-segmented VPN with per-application split
tunnels and continuous session re-authentication can implement many ZT tenets. The problem is that
most VPN deployments are not configured that way. They provide network-level access when what is
needed is application-level access.

A **reverse proxy** (Pomerium, BeyondCorp-style) shifts the access decision to the application
layer: every request hits the proxy, which authenticates the user (via OIDC), checks the device
posture signal, evaluates the access policy, and forwards the request to the upstream application
if it passes. The application is never exposed to the network — its listeners are only reachable
through the proxy. This pattern aligns very closely with the original BeyondCorp design and is
excellent for HTTP/S workloads. Its limitation is scope: it is protocol-specific (HTTP/S and a few
others), so it cannot replace VPN for arbitrary TCP/UDP workloads. For organizations that are 90%
web-based SaaS and on-premises HTTP applications, this is often the right first move.

A **network mesh** (Tailscale, headscale, Netbird) restores the "device has a private IP in a
trusted namespace" model, but cryptographically: every device is identified by a WireGuard public
key, traffic is peer-to-peer and encrypted, and the coordination server distributes ACLs that
determine which devices can reach which. The blast radius of a compromised device is limited to
what that device's tags allow. This pattern is excellent for infrastructure access (SSH, RDP,
internal APIs), scales well to remote workers and contractors, and does not require re-architecting
applications. Its limitation is that device trust depends on the coordination server's ACL
management; posture signals require integration with an MDM or EDR.

A **cloud edge** (Cloudflare Zero Trust, Zscaler, Netskope) moves enforcement to a globally
distributed edge: traffic from the device goes through the vendor's edge (via WARP or a browser
isolation session), where identity and posture are evaluated, before being forwarded to the
application. This is SASE in concrete form. The pattern provides excellent performance globally
(traffic exits at the nearest edge PoP), built-in threat inspection, and a single policy plane for
both on-premises and SaaS applications. The trade-off is dependency: the vendor's edge is now in
your data path, and your security posture is partly a function of their SLA, their abuse handling,
and their platform's configuration surface area.

The architectural insight that ties these together is **where the policy engine sits** and
**what it can observe at the time of the access decision**. A VPN evaluates identity at the network
perimeter, once. A reverse proxy evaluates identity and (optionally) posture at the application
entry point, per request. A network mesh evaluates device identity at the time of mesh
registration and ACL-based access per connection. A cloud edge evaluates identity, posture, and
threat signals per session with continuous re-evaluation. Each step up is more granular, more
dynamic, and — correctly implemented — harder for an attacker to abuse.

## Learn (~3 hrs)

**Architecture patterns (~1.5 hrs)**
- [Pomerium — Architecture Overview](https://www.pomerium.com/docs/internals/architecture) — the clearest documentation of the reverse-proxy ZTNA pattern: how the proxy sits in front of upstreams, how authentication and authorization are separated, and how the access policy is evaluated per request.
- [Tailscale — Network Design](https://tailscale.com/docs/concepts/what-is-tailscale) — Tailscale's overview of the WireGuard mesh model, coordination server, and ACL-driven access control. Read alongside the headscale lab from module 03.

**The BeyondCorp pattern (~1 hr)**
- [BeyondCorp: Design to Deployment at Google (2016)](https://research.google/pubs/beyondcorp-design-to-deployment-at-google/) — the second BeyondCorp paper, focusing on deployment. Read sections 2–4 to see how the access proxy, device inventory, and trust inference engine were assembled. This is the original reverse-proxy ZTNA in production.

**ADR format (~30 min)**
- [Architecture Decision Records — Michael Nygard (2011)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — the original ADR format post. Short. The structure (Context / Decision / Consequences) is what you'll use for the deliverable.

## Key concepts

- Four patterns: VPN (network perimeter), reverse proxy (application layer), network mesh (device identity), cloud edge (distributed enforcement)
- Policy engine placement: where in the stack is the access decision made, and what can it observe?
- Blast radius boundary: what does an attacker gain if this pattern is compromised?
- Protocol scope: reverse proxy = HTTP/S; mesh = arbitrary TCP/UDP; cloud edge = varies by product
- SASE = cloud edge + SD-WAN + security stack, delivered as a managed service

## AI acceleration

Use a model to draft the ADR template and pre-populate the comparison tables — it knows the vendor
landscape well. **Your critical review** is the "Consequences" section of the ADR: a model will
often list only positive consequences. Explicitly ask it to populate the negative and risky
consequences for each decision, then verify each against the actual product documentation. A model
that says Cloudflare Zero Trust has no single-vendor dependency risk is not being honest.
