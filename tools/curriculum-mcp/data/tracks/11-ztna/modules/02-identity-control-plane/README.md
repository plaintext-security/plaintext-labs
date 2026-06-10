# Module 02 — Identity as the Control Plane

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *when the perimeter dissolves, identity is the only boundary left.*

## Why this matters

In a Zero Trust model, the question "can this request proceed?" is answered by an access policy,
not by a firewall rule. And the anchor of every access policy is identity: who is the subject of
this request, can they prove it, and do they have standing to access this resource right now? If
your identity infrastructure is weak — shared passwords, federation trust you can't audit, tokens
that live for hours — your access model is weak regardless of what sits in front of the application.
Getting identity right is the prerequisite for everything else in the ZT stack.

## Objective

Deploy a Keycloak identity provider, seed it with the Meridian realm configuration, obtain a JWT
via an OIDC flow, and demonstrate how per-application access decisions are enforced through claims
— then reason about how Meridian's existing Okta/Entra ID would federate into the same pattern.

## The core idea

The mental model shift is simple but consequential: **identity is the new network perimeter.** Under
the old model, a Palo Alto firewall checked the source IP against a zone policy. Under ZT, a policy
engine checks a cryptographically signed identity assertion (a JWT, a SAML assertion, or an mTLS
certificate) against an access policy. The mechanics are different; the purpose is identical. The
advantage of the identity-based approach is that the assertion travels with the request across any
network — VPN or no VPN, on-premises or SaaS — and can be re-evaluated at every hop without the
request needing to be "inside" anything.

OpenID Connect (OIDC) is the protocol that makes this practical. When a user authenticates to a
Keycloak realm, they prove their identity (password, TOTP, passkey — whatever the realm requires),
and Keycloak issues a short-lived JWT access token signed with the realm's private key. That token
carries claims: `sub` (who), `aud` (what application), `groups` (what roles), `exp` (when it
expires). The application validates the signature against the realm's public key — no roundtrip to
an auth server on every request — and makes its access decision from the claims in the payload.
This is "identity as the control plane" in concrete form: the token is the pass, the signature is
the tamper-evident seal, and the application is the enforcer. No token, no access.

The enterprise version of this is **federation**: Meridian doesn't want a second identity silo for
the Keycloak realm; they want their Okta users to authenticate through Keycloak using SAML 2.0 or
OIDC federation. In federation, Keycloak becomes an identity broker — it trusts assertions from the
upstream IdP (Okta, Entra ID) and issues its own access tokens downstream to the application. From
the application's perspective, there is one issuer; from the user's perspective, they use their
familiar SSO flow. The critical operator skill is reading the federation trust configuration: which
attributes map to which claims, what the token lifetime policy is, and which groups from the
upstream IdP are trusted to grant elevated roles in the downstream application. These are exactly
the settings an attacker will try to manipulate in a token abuse scenario.

There are two gotchas that trip up identity-as-control-plane deployments. The first is **token
lifetime creep**: teams lengthen token expiry to avoid re-auth interruptions, and long-lived tokens
erode the per-request evaluation model that ZT depends on. A one-hour access token is fine for most
applications; a 24-hour token effectively restores session-based trust. The second is **claim
inflation**: organizations add roles to their token schema incrementally and never remove them. A
JWT that carries 40 group memberships from a sprawling AD sync is not fine-grained access control —
it's just VPN access re-packaged as JSON. The discipline is to define what claims the application
actually needs, issue only those, and scope the token to a single audience (`aud`) so it cannot
be replayed against a different application.

## Learn (~4 hrs)

**OIDC and JWTs (~1.5 hrs)**
- [The OAuth 2.0 Authorization Framework (RFC 6749)](https://datatracker.ietf.org/doc/html/rfc6749) — read sections 1–2 (introduction and roles) and section 4.3 (Resource Owner Password Credentials grant, which the lab uses). The RFC is the ground truth when vendor docs disagree.
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) — read sections 1–3 (overview and authentication flows). OIDC is the identity layer on top of OAuth 2.0; understanding the distinction (authorization vs. authentication) is foundational.
- [jwt.io](https://www.jwt.io/) — paste any JWT here to decode and inspect claims. Essential debugging tool; run through it during the lab.

**Keycloak (~1 hr)**
- [Keycloak documentation — Core Concepts](https://www.keycloak.org/docs/latest/server_admin/index.html#core-concepts-and-terms) — read "Core Concepts": realm, client, user, role, scope. 15 minutes; covers exactly the vocabulary you need for the lab.
- [Keycloak — Server Administration Guide: Identity Brokering and Social Login](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker) — the federation section: how Keycloak acts as a broker between an upstream IdP (Okta, Entra ID) and a downstream application. Read to understand the federated trust model.

**Identity attacks (~1 hr)**
- [MITRE ATT&CK T1528 — Steal Application Access Token](https://attack.mitre.org/techniques/T1528/) — how tokens are stolen and replayed; what the mitigations look like in an OIDC context. Short, directly applicable.
- [MITRE ATT&CK T1606.002 — SAML Tokens (Golden SAML)](https://attack.mitre.org/techniques/T1606/002/) — the identity-layer equivalent of a Golden Ticket; relevant when evaluating federation trust in Okta/Entra ID environments like Meridian's. Read the procedure examples.

**Token inspection (~30 min)**
- [jwt-cli (GitHub)](https://github.com/mike-engel/jwt-cli) — a command-line JWT decoder used in the lab. Install it, then `jwt decode <token>` to see claims in a readable format. Faster than copy-pasting into jwt.io during operations.

## Key concepts

- Identity is the ZT control plane: every access decision anchors to a verifiable identity assertion
- OIDC token flow: authentication → token issuance → claim validation → access decision
- JWT anatomy: header (algorithm), payload (claims: sub, aud, groups, exp), signature
- Federation broker pattern: Keycloak as the broker between Okta/Entra ID upstream and applications downstream
- Token lifetime discipline: short-lived tokens preserve the per-request evaluation model
- Claim minimization: issue only the claims the application needs, scoped to a single audience

## AI acceleration

A model can generate Keycloak realm JSON exports and `curl` OIDC flows quickly, and the output is
usually syntactically correct. **Your review job** is to verify the token lifetime and scope
settings reflect ZT discipline (not defaults, which are often permissive), and to trace every claim
in the issued JWT back to a deliberate policy decision rather than an inherited default. Ask the
model to explain each realm setting it generated before you run it — if it can't justify `accessTokenLifespan: 300` versus `3600`, you don't know what you're running.
