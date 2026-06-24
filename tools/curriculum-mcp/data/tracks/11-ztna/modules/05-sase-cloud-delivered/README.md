# Module 05 — SASE & Cloud-Delivered Zero Trust

*Type 7 · Build-&-Operate — publish an app through a SASE tunnel with an identity-aware Access policy and no inbound ports; the deliverable is the working zero-inbound deployment plus a verified unauthenticated-denial check. (Secondary: Design → Red-team-your-own.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *publish a private app to the internet with zero inbound ports, gated at a global edge — then prove an unauthenticated request can't reach it.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

Module 04 made you decide the *architecture*. This module makes you ship one and operate it. The
fastest path from "we decided on Zero Trust access" to "a private app is live, authenticated, and
has no open ports" — for a small team without a data-centre — is a cloud-delivered SASE edge.

The win is concrete and you build it: an internal app published to anyone on the planet through a
vendor's global edge, where the app itself **opens no inbound ports at all**. `cloudflared` dials
*out* to the edge; the edge enforces your access policy and only then forwards the request. An
attacker who scans your server's IP finds nothing listening — there is no socket to hit. That
inverts the reverse-proxy model you've run for years, and it's why this is the most common first
real ZTNA deployment a three-person security team actually ships. The thing you walk away with is
the running, gated, no-inbound-ports service — plus the proof that an unauthenticated request is
turned away.

## Objective

Stand up Cloudflare Zero Trust (free tier, 50 users, no expiring trial), run a `cloudflared`
tunnel that publishes a local nginx container with **no inbound ports**, gate it behind an Access
policy requiring email verification, and **prove denial**: an unauthenticated request reaches the
login page, never the app. Then defend the build-vs-buy call — when cloud-delivered beats
self-hosted, and when it doesn't — and red-team your own design by confirming nothing listens.

## The core idea

SASE — Secure Access Service Edge, the term Gartner coined in its 2019 "The Future of Network
Security Is in the Cloud" report — names the convergence of networking (SD-WAN) and security (ZTNA,
CASB, SWG, FWaaS) into one cloud-delivered service. The practitioner translation is shorter: SASE
is the *managed* version of the Zero Trust networking stack you built by hand in Modules 02–06.
Instead of running and patching a Pomerium proxy and a Headscale coordination server yourself, you
rent a vendor's global edge that provides those controls — and more — as a service.

The architectural core is the **tunnel**. `cloudflared` runs next to your app and opens an
*outbound-only* encrypted connection to the edge. No inbound ports, no firewall rule, no listener.
The app is unreachable from the internet unless the request arrives through the edge — which
evaluates your **Access policy** first. That policy is an ordered rule list (allow this email / this
domain / this IdP group / this device-posture check), and the building blocks are additive: email
OTP today, federated SSO tomorrow, posture-gated access after that, with the tunnel model unchanged.
The gotcha to internalise: `include` is an **OR** (any matching rule lets you in) and `require` is
an **AND** (every rule must hold). A policy with only `include: any @company.com email` and no
`require` clause is syntactically valid and wide open — the implicit-trust bug, restored one layer up.

**The load-bearing judgment of this module is build-vs-buy: cloud-delivered SASE vs self-hosted
ZTNA — and you must defend the call.** It is *not* "the cloud always wins." The honest axis is
**ops burden vs control**. Cloud-delivered wins when the team is small and the toil of running and
patching your own proxies dominates — the vendor operates the global edge, DDoS scrubbing, and the
policy console, and you ship in an afternoon. Self-hosted wins when the data path itself is the
risk you're managing: a regulated environment that can't route plaintext (or even TLS-terminated)
traffic through a third party, an air-gapped or sovereignty-constrained network, a vendor whose SLA
you can't make your security floor, or a scale where per-seat pricing breaks the model. The thing
cloud-delivered buys you in convenience, it sells you in **dependency**: the vendor is now in your
data path, their availability SLA is the floor of your security posture, and their (substantial)
config surface is a new place to misconfigure. There is no universally right answer — there is the
answer you can defend for *this* environment, and that defence is part of the deliverable.

**Now red-team your own design.** Deploying a no-inbound-ports service and *claiming* it holds are
two different things; the module ends in the difference. The same logic that makes the model strong
makes the test cheap: because the security is "there is no listener," you prove it by trying to find
one. Confirm the origin port is bound to localhost only and is not reachable from another network;
confirm an unauthenticated browser hits the Access login page, never the app. Then count the
attacker's cost honestly. Against a VPN-fronted flat network, a single stolen credential plus a
reachable VPN endpoint is often the whole game (it was, in the Colonial Pipeline intrusion that
opened this track — one legacy VPN account with no MFA). Against this design, the attacker first
has to find something to attack: there's no exposed port to scan, no proxy in front to fingerprint,
and reaching the app demands passing edge auth *and* (when you add it) device posture. You haven't
made the app invincible — you've removed the cheap front door and forced the attacker up the cost
curve. State what's left: a stolen valid session, a compromised enrolled device, a vendor-side
compromise. That residual is the honest output of red-teaming your own design.

## Learn (~3 hrs)

*Build-first: the model above is yours to own. These get you to a working tunnel and a defensible
build-vs-buy call — read them to ship the lab, not to relearn Zero Trust.*

**Cloudflare Zero Trust — get the tunnel up (~1.5 hrs)**
- [Cloudflare Zero Trust — Getting started](https://developers.cloudflare.com/cloudflare-one/setup/) (~45 min, do it) — the official setup. Work "Getting started" then "Connections → Tunnels"; the lab follows this closely and the docs are current.
- [Cloudflare Tunnel — how the connector works](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/) (~25 min) — why the connection is outbound-only and how the edge routes to your origin. This *is* the "no inbound ports" mechanism — read it until you can explain why an IP scan of your server finds nothing.
- [Cloudflare Access — policies (include / require / exclude)](https://developers.cloudflare.com/cloudflare-one/policies/access/) (~20 min, the key page) — the OR-vs-AND rule semantics. Read `include` vs `require` carefully; this is the field where "syntactically valid" and "wide open" coincide.

**SASE & the build-vs-buy frame (~1 hr)**
- [NIST SP 800-207 — Zero Trust Architecture](https://csrc.nist.gov/pubs/sp/800/207/final) (~30 min, read §2 tenets + §3 logical components) — the vendor-neutral model SASE is one delivery of; gives you the language to argue self-host vs cloud-delivered on architecture, not marketing.
- [Cloudflare — Argo/Cloudflare Tunnel announcement (2018)](https://blog.cloudflare.com/argo-tunnel/) (~20 min) — the original "no inbound ports" pitch, shorter and clearer than the docs; read it for the security-model argument, then ask where the *dependency* it doesn't mention bites.

**The honest tradeoff (~30 min)**
- Gartner, "The Future of Network Security Is in the Cloud" (Lawrence Orans, Joe Skorupa, Neil MacDonald; 30 Aug 2019) — the report that coined SASE (now Gartner-gated; read a summary if you can't access the full note). Where SASE comes from and what convergence it claims; read it skeptically, as the vendor-side case you'll weigh against control and lock-in.

## Key concepts

- SASE = the *managed* ZT networking stack (ZTNA + CASB + SWG + FWaaS + SD-WAN) from a global edge, not an appliance
- `cloudflared` tunnel: outbound-only encrypted dial to the edge → **no inbound ports, no listener to scan**
- Cloudflare Access: edge policy engine; building blocks are additive (email OTP → SSO → device posture)
- `include` is OR, `require` is AND — the field where "valid policy" and "wide open" coincide
- **Build-vs-buy is the judgment**: ops-burden vs control — cloud-delivered wins for small teams; self-hosted wins when the data path / sovereignty / SLA / scale is the risk
- Vendor dependency is the price: the edge SLA is your security floor; the config surface is a new misconfig source
- Red-team-your-design: prove "no listener" by trying to find one; the deliverable includes the *failed* unauthenticated reach

## AI acceleration

Cloudflare Access policy JSON is well-structured and a model emits syntactically correct examples
fast — which is exactly the trap. **Your review job is to verify the policy is as *restrictive* as
you intend, not just valid.** Two failures recur: the model reaches for `include` where you need
`require` (turning an AND into an OR, so a posture check that was meant to *also* hold becomes an
alternative way in), and it uses deprecated field names the dashboard silently won't honour. Check
every `include` / `require` / `exclude` against the current Cloudflare docs, and confirm there is at
least one `require` clause anywhere your intent is "AND". Then do the one test a model can't do for
you: attempt access with a credential that *should be denied*, and confirm it is. AI drafts the
policy → you prove the deny path → you own the gate.
