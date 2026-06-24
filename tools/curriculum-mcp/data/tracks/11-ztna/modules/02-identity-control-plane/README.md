# Module 02 — Identity as the Control Plane

*Type 7 · Build-&-Operate — stand up a working identity provider and run the full OIDC token flow through it; the deliverable is the running IdP and a minted, signature-validated token, not an essay. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *when the perimeter dissolves, identity is the only boundary left — so the keys that sign identity are the crown jewels.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

In a Zero Trust model the question "can this request proceed?" is answered by an access policy, not by
a firewall rule — and the anchor of every access policy is identity: who is the subject, can they prove
it, and do they have standing to reach this resource *right now*? That answer rides on a cryptographic
assertion (a JWT, a SAML assertion, an mTLS cert) signed by the identity provider's private key. Which
means the IdP's signing key is no longer one secret among many: **it is the master key to every access
decision in the estate.** Whoever holds it doesn't need a password, an MFA prompt, or a session — they
can *mint* a valid identity for anyone, for any application.

That is not a thought experiment. In **Storm-0558 (2023)**, a China-aligned actor obtained a Microsoft
consumer (MSA) signing key and used it to **forge authentication tokens**, reaching the email of
roughly **25 organizations** — including the U.S. Departments of State and Commerce and Congressional
staff — with no credential theft and no MFA bypass: the forged token *was* the credential. Microsoft's
own investigation traced the key to a 2021 crash dump that should never have contained it, recovered
after an engineer's account was compromised. The U.S. **Cyber Safety Review Board** (CSRB, April 2024)
called the intrusion **preventable** and faulted Microsoft's security culture. The lesson for this
module is direct: standing up an IdP is the easy half; understanding that its signing key, token
lifetime, and claim scope *are* your blast-radius controls is the half that makes you an architect.

## The core idea

The mental-model shift is small but consequential: **identity is the new network perimeter.** Under the
old model a firewall checked source IP against a zone. Under Zero Trust a policy engine checks a
cryptographically signed identity assertion against an access policy. The mechanics differ; the purpose
is identical — and the assertion travels *with* the request across any network, so it can be
re-evaluated at every hop without the request ever being "inside" anything.

**OpenID Connect (OIDC)** is what makes this practical, and the architecture you build in the lab is the
canonical shape. A user authenticates to a Keycloak realm (password, TOTP, passkey — whatever the realm
requires); Keycloak issues a short-lived JWT signed with the realm's **private** key. The token carries
claims — `sub` (who), `aud` (which application), `realm_access.roles` (what they may do), `exp` (when it
dies). The application validates the **signature against the realm's public key** — published at the
JWKS endpoint, no round-trip to the auth server per request — and decides access from the claims alone.
That is "identity as the control plane" in concrete form: the token is the pass, the signature is the
tamper-evident seal, and the application is the enforcer. *No valid signature, no access* — which is
exactly why the private key is the crown jewel, and why a forged-token incident like Storm-0558 is
catastrophic rather than merely bad.

The enterprise version of this is **federation**, and reasoning about it is the operator skill that
separates "I ran the tutorial" from "I can run the IdP." An organization rarely wants a second identity
silo, so Keycloak runs as an **identity broker**: it trusts assertions from an upstream IdP (Okta, Entra
ID) over SAML 2.0 or OIDC and issues *its own* downstream tokens to the application. To the app there is
one issuer; to the user, their familiar SSO. The judgment is in the trust mapping — which upstream
attributes map to which downstream claims, and *which upstream groups are trusted to grant elevated
roles*. Get that mapping wrong and the upstream IdP silently dictates your authorization. (Golden SAML,
MITRE ATT&CK T1606.002, is the federation-trust equivalent of the Storm-0558 forge: steal the SAML
signing key and you mint trusted assertions at will.)

**The one load-bearing judgment — token lifetime and claim scope are blast-radius controls, not
defaults to accept.** Two failure modes recur. *Token-lifetime creep*: teams stretch `exp` to avoid
re-auth interruptions, and a 24-hour access token quietly restores session-based trust — undoing the
per-request evaluation Zero Trust depends on, and widening the window a forged or stolen token stays
live. *Claim inflation*: roles get added to the token schema and never removed, so a JWT carrying 40
group memberships from a sprawling AD sync isn't fine-grained access control — it's VPN access
re-packaged as JSON. The discipline: issue only the claims the application needs, keep `exp` short, and
scope each token to a single audience (`aud`) so it cannot be replayed against a different application.
Every one of those settings is a number you must be able to *defend*, not a default you inherited.

## Learn (~4 hrs)

**OIDC and JWTs (~1.5 hrs)**
- [The OAuth 2.0 Authorization Framework (RFC 6749)](https://datatracker.ietf.org/doc/html/rfc6749) — read sections 1–2 (introduction and roles) and section 4.3 (Resource Owner Password Credentials grant, which the lab uses). The RFC is the ground truth when vendor docs disagree.
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) — read sections 1–3 (overview and authentication flows). OIDC is the identity layer on top of OAuth 2.0; understanding authorization vs. authentication is foundational.
- [jwt.io](https://www.jwt.io/) — paste any JWT to decode and inspect claims. Essential debugging tool; run a token through it during the lab.

**Keycloak (~1 hr)**
- [Keycloak documentation — Core Concepts](https://www.keycloak.org/docs/latest/server_admin/index.html#core-concepts-and-terms) — read "Core Concepts": realm, client, user, role, scope. ~15 min; exactly the vocabulary the lab uses.
- [Keycloak — Server Administration Guide: Identity Brokering and Social Login](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker) — the federation section: how Keycloak brokers between an upstream IdP (Okta, Entra ID) and a downstream application. Read for the federated trust model.

**Why the signing key is the crown jewel (~1 hr)**
- [Microsoft — Analysis of Storm-0558 techniques for unauthorized email access](https://www.microsoft.com/en-us/security/blog/2023/07/14/analysis-of-storm-0558-techniques-for-unauthorized-email-access/) (~20 min) — the first-party writeup of how a stolen consumer signing key was used to forge tokens against Exchange Online. Read it as a concrete answer to "what happens if the IdP private key leaks."
- [MITRE ATT&CK T1606.002 — SAML Tokens (Golden SAML)](https://attack.mitre.org/techniques/T1606/002/) — the federation-layer equivalent: forge trusted assertions by stealing the signing key. Directly relevant when you reason about the federation mapping in the lab.
- [MITRE ATT&CK T1528 — Steal Application Access Token](https://attack.mitre.org/techniques/T1528/) — the everyday cousin of forgery: stealing the issued token. What `aud` and short `exp` are defending against. Short, directly applicable.

**Token inspection (~30 min)**
- [jwt-cli (GitHub)](https://github.com/mike-engel/jwt-cli) — a command-line JWT decoder used in the lab. Install it, then `jwt decode <token>` to read claims faster than copy-pasting into jwt.io during operations.

## Key concepts

- **Identity is the ZT control plane** — every access decision anchors to a verifiable identity assertion, so the **signing key is the crown jewel** (Storm-0558: a stolen key forged tokens, no credential needed).
- **OIDC token flow:** authenticate → IdP signs a short-lived JWT → application validates the signature against the JWKS public key → access decision from claims.
- **JWT anatomy:** header (algorithm), payload (`sub`, `aud`, `realm_access.roles`, `exp`), signature.
- **Federation broker pattern:** Keycloak brokers an upstream IdP (Okta/Entra ID) to downstream apps; the attribute→claim and group→role mapping *is* the trust decision (Golden SAML is its abuse).
- **Token lifetime is a blast-radius control:** short `exp` preserves per-request evaluation and shrinks the window a forged/stolen token stays live.
- **Claim minimization + single `aud`:** issue only what the app needs and scope to one audience so the token can't be replayed elsewhere.

## AI acceleration

A model will generate Keycloak realm JSON and `curl` OIDC flows quickly, and the output is usually
syntactically correct — which is the trap. **Your review job:** verify the token-lifetime and scope
settings reflect ZT discipline rather than the permissive defaults a model tends to emit, and trace
every claim in the issued JWT back to a deliberate policy decision. The sharpest review move is on the
*validation* code (the lab's `validate-token.py`): a model will happily produce a "validator" that
base64-decodes the payload and skips the signature, or one that accepts `alg: none` — that is not a
validator, it's the Storm-0558 failure mode in script form. Ask the model to justify each realm setting
before you run it: if it can't defend `accessTokenLifespan: 300` versus `3600`, you don't yet know what
you're running, so you don't yet own it.
