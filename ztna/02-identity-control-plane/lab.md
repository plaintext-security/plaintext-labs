# Lab 02 — Identity as the Control Plane: stand up Keycloak, then prove the signature

> **Hands-on lab.** Environment: `plaintext-labs/ztna/02-identity-control-plane`.
> Objective: **run the OIDC token flow end-to-end and validate a token's signature against the realm's
> public key.** Target: **~90 min**, one finish line. This is a **Build-&-Operate lab — a real Keycloak
> container.** The working IdP + a validator you watched reject a forged token is the proof.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The signing key is the crown jewel.** | A stolen key *forges* valid identities — no password, no MFA, no session (Storm-0558; Golden SAML). |
| 2 | **Validate the SIGNATURE against JWKS — never trust a decoded payload.** | base64-decode ≠ validate. Accepting `alg: none` is the Storm-0558 failure in Python. |
| 3 | **Token lifetime is a blast-radius control** (this realm: `exp` = 300 s). | A long `exp` restores session trust and widens the stolen/forged-token window. |
| 4 | **Scope to a single `aud` + minimal claims.** | Blocks cross-app replay; a 40-role JWT is VPN access re-packaged as JSON. |
| 5 | **Federation broker: the upstream group→role map IS the trust decision.** | Wrong map hands your authz to the upstream IdP; Golden SAML (T1606.002) forges that seam. |
| 6 | **The real handles:** realm `corp`, client `corp-app` / secret `corp-app-secret`, users `analyst` / `analyst123` and `admin` / `admin456`. | These are the exact strings you type; the module prose used placeholders. |

*(If you can explain all six cold at the end — especially #1 and #2 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [OIDC token flow](README.md#oidc-the-token-flow-youre-about-to-run), the
> [validation gates](README.md#validation-is-a-chain-of-gates-not-a-base64-decode), and the
> [stolen-token-vs-stolen-key table](README.md#the-case-forge-the-assertion-skip-everything-else).

---

## Warm-up — answer before you start the container (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A validator that base64-decodes the JWT payload and reads `realm_access.roles` from it — **why is
   that not a validator at all**, and which one line of the module's validation flowchart does it skip?
2. Name the **two** numbers in this realm that bound blast radius, and say what each one limits when a
   token is stolen. (Hint: one is on the clock, one is on the destination.)

---

## Setup

This is a **reference lab** with a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs **Keycloak 24 in
Docker** with the `corp` realm imported from `data/corp-realm.json` on startup.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/02-identity-control-plane
make up      # start Keycloak; waits until the corp realm actually issues a token (~60s)
make demo    # walk the OIDC flow: mint a JWT for analyst + admin, decode claims, list JWKS keys
make down    # stop when done   (make reset tears down container + volumes)
```

Keycloak comes up on `http://localhost:8080`; the admin console is at `http://localhost:8080/admin`
(`admin` / `admin` — local dev only, never production). The `corp` realm lives at
`http://localhost:8080/realms/corp`.

> **▸ On track if:** `make up` prints `Keycloak is ready.` after a run of dots (it polls the real token
> endpoint, so a ready message means users and clients are fully imported, not just that the server
> booted). If it prints `did not become ready in time`, read the logs it dumps and re-run `make up`.

> **Authorization note.** Everything here runs locally against a container **you** started; no external
> service is contacted. The authorization rule still stands for the rest of the track: only test systems
> you own or have explicit written permission to test. The forged-token step below is performed against
> *your own* lab token — never against a real IdP.

---

## Build it — read a little, do a little

### Step 1 — Run the flow and read what the IdP actually minted

**Concept (30 sec):** Flight-card #1 + #6. `make demo` is the whole OIDC token flow compressed into one
command: it authenticates two users, prints their decoded JWTs, and lists the realm's public keys. Read
the claims like an enforcer would — the token *is* the access decision.

**Do it:** run `make demo`. In the analyst payload, locate `preferred_username`, `azp`,
`realm_access.roles`, and `exp`. Then paste the raw analyst token (grab it yourself in step 2, or from
the demo output) into [jwt.io](https://jwt.io/) and confirm the header names an **asymmetric** algorithm
(RS256), not `none` or an HMAC.

> **▸ On track if:** the demo banner reads *"Lab 02 — OIDC Token Demo: Corp realm"*, the analyst payload
> shows `realm_access.roles` containing **`analyst`**, `azp` is **`corp-app`**, and the closing lines note
> the token **expires in 300 seconds**. Step 3 of the demo prints the JWKS **Key ID** and **Alg: RS256** —
> that public key is what your validator will fetch.

### Step 2 — Mint a token yourself, then diff analyst vs admin

**Concept (30 sec):** Flight-card #4. Claim-based access control means the *app* decides from
`realm_access.roles`, not from a network zone. The only difference between these two users is the roles
in the token — that difference is the authorization.

**Do it:** obtain the analyst token by hand with the real client credentials:

```bash
curl -s -X POST http://localhost:8080/realms/corp/protocol/openid-connect/token \
  -d "grant_type=password" -d "client_id=corp-app" -d "client_secret=corp-app-secret" \
  -d "username=analyst" -d "password=analyst123" -d "scope=openid" | python3 -m json.tool
```

Decode the `access_token` (with `jwt decode <token>`, or pipe the middle segment through
`base64 -d`). Repeat for **admin** (`username=admin`, `password=admin456`) and write down which claims
differ.

> **▸ On track if:** the JSON response carries an `access_token`, `expires_in: 300`, and a
> `refresh_token`. `analyst` decodes to `realm_access.roles` = **`["analyst", ...]`**; `admin` decodes
> to roles including **both `analyst` and `admin`**. If the two role sets look identical, you decoded the
> same token twice — re-run with the admin credentials.

### Step 3 — Find the blast-radius controls in the realm

**Concept (30 sec):** Flight-card #3. Token lifetime and client scope aren't cosmetic — they are the
numbers that decide how long a stolen token lives and how far it reaches. You're going to *defend* them,
so first read them straight from the source.

**Do it:** open `data/corp-realm.json` (or the admin console → Realm Settings → Tokens). Read
`accessTokenLifespan`, and note that the realm ships with `bruteForceProtected: true` and an **empty**
`identityProviders` array. Then find the **second** client, `corp-api`: note its `access.token.lifespan`
of 60 s and that `directAccessGrantsEnabled` is `false`. Write one sentence defending *why* 300 s (not
3600) is the right call for `corp-app`.

> **▸ On track if:** you can state that `corp-app` issues **300 s** access tokens and `corp-api` issues
> **60 s**, that federation is **not yet configured** (empty `identityProviders`), and that brute-force
> protection is on. These are the facts your memo and validator lean on.

### Step 4 — Reason about the two abuses: stolen token vs stolen key

**Concept (30 sec):** Flight-card #1 + #5. This is the module's spine. A stolen *token* is bounded by
`exp` and `aud`; a stolen *signing key* is bounded by nothing you can revoke fast — that is the
Storm-0558 / Golden SAML gap.

**Do it (write it, don't run it):** in your deliverable, answer three things. (a) If an attacker phishes
the analyst's JWT, what can they reach and for how long, and what would a tight `aud` prevent? (b) Why is
a stolen **signing key** categorically worse — and *what exactly would have to leak from this Keycloak
realm* for the Storm-0558 scenario to apply here? (c) The federation seam: `identityProviders` is empty;
describe what you'd add to broker **Okta** as an upstream OIDC IdP (`authorizationUrl`, `tokenUrl`,
`clientId`, `clientSecret`), the mapper that turns Okta's `groups` claim into `corp` roles, and the trust
risk — Okta group membership becoming *your* app's authorization, the exact seam Golden SAML / **T1606.002**
abuses. Label this a config-level design, not something you stood up.

> **▸ On track if:** your stolen-token mitigations are **short `exp` + single `aud`**, your
> stolen-key answer names the **realm signing key** as the thing that must not leak, and your federation
> paragraph ends on the **group→role mapping** as the trust decision — not on the OIDC endpoints.

---

## Prove the control (your finish line)

One check proves you built a **validator**, not a decoder. Run `validate-token.py` (below) three times
against your running realm and *watch* the outcomes:

> 1. a **real** token minted in step 2 → **accepted**, claims printed;
> 2. a token with one character flipped in the payload → **rejected** (signature fails);
> 3. a hand-crafted **`alg: none`** token → **rejected** (weak algorithm refused).

**The proof is the two rejections.** A script that prints claims from a real token but *also* accepts the
tampered or unsigned one is the Storm-0558 failure mode in miniature — there is no grader here; watching
it reject the forgery is your self-check. Assemble `oidc-analysis.md` alongside it.

---

## Recall check — close the docs, answer from memory (3 min)

1. Walk the OIDC flow from "user clicks login" to "app allows the request" — where does the signature
   get *created*, and where does it get *checked*?
2. Your validator rejected two tokens. Which gate in the validation chain caught the tampered one, and
   which caught the `alg: none` one?
3. Stolen token vs stolen signing key: which is bounded by `exp`/`aud`, which is bounded by nothing you
   can revoke fast, and which incident proved the second?

Missed one? Re-run the step that built it, or pull the [validation-gates section](README.md#validation-is-a-chain-of-gates-not-a-base64-decode) — then re-answer.

---

## Deliverables

- **`oidc-analysis.md`** — containing: the decoded claims for **both** `analyst` and `admin` (keep the
  payload, redact the signature); which claims differ and the access decision each produces; your defense
  of the `accessTokenLifespan: 300` setting; the token-abuse scenario with your stolen-token mitigation
  **and** the stolen-signing-key contrast (step 4b); and the Okta federation paragraph (step 4c), labelled
  assessed-from-config.
- **`validate-token.py`** — the working validator from *Automate & own it*, committed with it.

*Lab artifacts — raw tokens, the realm export, keys — stay out of commits. Never commit a live JWT.*

## Automate & own it

**Required.** Write `validate-token.py` that:

1. Takes the Keycloak token URL and user credentials as arguments.
2. Obtains a JWT via the Resource Owner Password Grant against `corp-app`.
3. **Validates the token's signature** against the realm's public key, fetched from the JWKS endpoint —
   `http://localhost:8080/realms/corp/protocol/openid-connect/certs`.
4. Prints the claims and flags if the token is within 60 seconds of expiry.

Have a model draft it; **you review every line — especially the signature path.** Tell it explicitly:
*"verify the signature against the JWKS public key; reject `alg: none` and any symmetric algorithm."* A
script that accepts an unsigned token or skips verification is not a validator, it's the Storm-0558
failure mode. **Before you commit, prove it both ways** (the finish line above): it accepts a real token
and *rejects* a base64-tampered one and an `alg: none` one. That observed rejection — not clean syntax —
is what lets you say you own it.

## Definition of done (`identity-control-plane` ✅)

- [ ] `make up` reports `Keycloak is ready.` and `make demo` prints decoded JWTs for analyst and admin
  plus the JWKS key (RS256).
- [ ] You have manually minted and decoded tokens for **both** users via `curl` and can list the claims
  that differ and the access decision each drives.
- [ ] Your memo defends `accessTokenLifespan: 300`, contrasts a stolen token (bounded by `exp`/`aud`)
  with a stolen signing key (Storm-0558 / Golden SAML), and names what would have to leak from *this*
  realm for the key scenario to apply.
- [ ] The Okta federation paragraph names the group→role mapping as the trust decision and cites
  T1606.002.
- [ ] `validate-token.py` accepts a real token and you have **watched it reject** both a tampered token
  and an `alg: none` token.
- [ ] `oidc-analysis.md` + `validate-token.py` are committed; you can explain all six flight-card facts cold.

## Connects forward

- **Module 03 — Device Trust & Posture** binds *device* identity to the access decision alongside the
  user identity you just proved — the next layer of the ZT stack.
- **Module 05 — SASE** uses a cloud enforcement point that consumes OIDC identity claims from an upstream
  IdP in exactly this pattern (issuer URL + JWKS endpoint for validation).
- **Module 11 — Red-team your own ZT deployment** attacks the federation trust seam you reasoned about
  here: forge the identity assertion and see whether the design holds.

## Marketable proof

> "I can deploy an OIDC identity broker, walk a JWT token flow end-to-end *including signature validation
> against the JWKS endpoint*, and reason about token-abuse and signing-key-compromise blast radius and
> federation trust risk — the core skills for a Zero Trust identity architect or IAM engineer."

## Stretch

- **Audience enforcement.** The realm already ships a second client, `corp-api` (service-account only,
  60 s tokens). Show that a `corp-app` access token is *not* valid for a resource that expects the
  `corp-api` audience — `aud` enforcement that stops cross-app token replay.
- **Brute-force lockout.** The realm has `bruteForceProtected: true`. Script repeated bad-password logins
  for `analyst`, trigger the lockout, and document exactly what an attacker learns (or doesn't) from the
  error response.
- **Map to ATT&CK.** Tie your two abuse scenarios to **T1528** (Steal Application Access Token) and
  **T1606.002** (Golden SAML), and write one sentence on which realm setting is the control for each.
