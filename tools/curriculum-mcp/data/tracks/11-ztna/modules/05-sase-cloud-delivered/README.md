# Module 05 — SASE & Cloud-Delivered Zero Trust

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *SASE is Zero Trust principles delivered as a managed global edge, not a data-centre appliance.*

## Why this matters

The four previous modules covered the principles, identity layer, device trust, and architecture
patterns of Zero Trust. SASE (Secure Access Service Edge) is what happens when you take ZT
principles — never trust, always verify, per-session evaluation — and deliver them from a
globally distributed edge rather than from a data-centre appliance you manage. For a 3-person
security team at a mid-size firm, SASE often represents the fastest path to measurable ZT progress:
the control plane is managed by the vendor, the policy surface is a web console, and applications
can be published without opening inbound firewall ports. This module is where the design from Lab
04 becomes hands-on reality.

## Objective

Sign up for Cloudflare Zero Trust (free tier, 50 users, no trial expiry), deploy a `cloudflared`
tunnel to publish a local nginx container as a private application, and gate access to it with an
Access policy that requires email verification — demonstrating Zero Trust application access with
no inbound network exposure.

## The core idea

The term SASE was coined by Gartner in 2019 to describe the convergence of networking (SD-WAN) and
security (ZTNA, CASB, SWG, FWaaS) into a cloud-delivered service. The practitioner translation is
simpler: SASE is the "managed service" version of the ZT networking stack. Instead of running a
Pomerium reverse proxy and a headscale coordination server yourself, you use a vendor's globally
distributed edge that provides all of those controls — and more — as a service. Cloudflare Zero
Trust is the most accessible entry point to this model (genuinely free for 50 users, no
expiring trial) and is also the vendor many security teams are evaluating or have deployed.

The architectural core of Cloudflare Zero Trust is the **tunnel**. `cloudflared` is a lightweight
daemon that runs next to your application — on the same Docker network, in a sidecar container, on
a VM — and creates an outbound-only encrypted connection to Cloudflare's edge. No inbound ports.
No firewall rules. The application is literally not reachable from the internet unless a request
comes through Cloudflare's edge, which enforces your Access policy before forwarding it. The
security model is the inverse of a traditional reverse proxy: instead of the proxy sitting in
front of your application and receiving inbound connections, your application reaches out to the
edge. An attacker who discovers your server's IP gets nothing — there is no listener.

Cloudflare Access is the policy engine that sits on the edge. A policy is an ordered list of rules:
allow this email / this email domain / this identity provider group / this device posture check.
"Require email OTP" is the simplest policy: Cloudflare sends a one-time code to the user's email,
which they enter in a browser, after which a short-lived JWT is issued and the request is forwarded
to your application. The step up to full SSO is minor: configure Cloudflare to authenticate via
your existing Okta or Entra ID OIDC provider instead. The step up to posture-gated access requires
the WARP client and a device posture check configured in the policy. Each step is additive; the
tunnel model does not change.

The SASE stack is broader than application access. Cloudflare Zero Trust also includes Gateway (a
DNS and HTTP proxy that filters malware, phishing, and shadow IT), Browser Isolation (a remote
browser that renders untrusted sites in Cloudflare's cloud, not the user's device), and CASB
(cloud app security broker for SaaS posture). For the purposes of this module, the lab focuses on
the ZTNA component — private application access via tunnel — because it is the component that
directly addresses the Meridian gap analysis finding from Lab 01. The broader stack is worth
knowing about because it describes the full control surface a SASE-maturity organization has.

The key limitation of cloud-edge SASE that a practitioner must be honest about is **vendor
dependency**. The vendor is now in your data path. Their availability SLA is your security posture's
floor. Their pricing model determines whether you can scale. Their configuration surface — which is
substantial in Cloudflare's case — creates new misconfigurations if you're not careful.
Organizations that deploy SASE as a "set and forget" managed service often end up with overly
permissive Access policies (e.g. "allow anyone with a @company.com email" with no posture check)
that restore the implicit trust problem in a new layer. The operational discipline is the same as
any ZT enforcement point: minimum access, explicit policy, regular review.

## Learn (~3 hrs)

**Cloudflare Zero Trust (~1.5 hrs)**
- [Cloudflare Zero Trust documentation — Getting started](https://developers.cloudflare.com/cloudflare-one/setup/) — the official setup guide. Read "Getting started" and "Connections → Tunnels" before the lab. The documentation is accurate and current; the lab follows it closely.
- [cloudflared Tunnel — How it works](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/) — the technical explainer for the tunnel architecture: why outbound-only tunnels are the security model, and how the edge routes traffic.

**SASE concepts (~1 hr)**
- [NIST Cybersecurity Framework & Zero Trust Principles](https://www.nist.gov/cyberframework) — U.S. government guidance on Zero Trust principles and architecture; foundational concepts behind SASE components (ZTNA, CASB, SWG).

**Tunnel security model (~30 min)**
- [Cloudflare Blog — Introducing Cloudflare Tunnel (2018)](https://blog.cloudflare.com/argo-tunnel/) — the original tunnel announcement; explains the "no inbound ports" security model and why it matters. Shorter and more readable than the full documentation.

## Key concepts

- SASE = ZT networking + SD-WAN convergence delivered from a global edge, not a data-centre appliance
- `cloudflared` tunnel: outbound-only encrypted connection to Cloudflare edge; no inbound ports
- Cloudflare Access: policy engine on the edge (email OTP → SSO → device posture, additive)
- Access policy components: identity rules (email, domain, IdP group) + device posture + context
- Gateway / Browser Isolation / CASB: the broader SASE stack beyond ZTNA
- Vendor dependency risk: edge SLA = security posture floor; WARP agent = endpoint coverage dependency

## AI acceleration

Cloudflare Access policy JSON is well-structured and a model generates syntactically correct
examples quickly. **Your review job** is to verify the policy rules are as restrictive as you
intend: an "allow everyone" rule is syntactically valid but the opposite of ZT. Check the
`include`, `require`, and `exclude` rule types — `include` is an OR condition; `require` is an AND.
A policy with only an `include: email: anyone@anywhere.com` rule and no `require` clause is open
to anyone with that domain email. Always test the policy by attempting access with a credential
that should be denied before calling it done.
