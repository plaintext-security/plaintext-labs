# Lab 02 — Identity as the Control Plane: stand up Keycloak, then prove the signature

> **Hands-on lab.** Environment: `plaintext-labs/ztna/02-identity-control-plane`.
> Objective: **run the OIDC token flow end-to-end and validate a token's signature against the realm's
> public key.** Target: **~90 min**, one finish line. This is a **Build-&-Operate lab — a real Keycloak
> container.** The working IdP + a validator you watched reject a forged token is the proof.

---

## ✈ Flight card — the 7 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The signing key is the crown jewel.** | A stolen key *forges* valid identities — no password, no MFA, no session (Storm-0558; Golden SAML). |
| 2 | **Validate the SIGNATURE against JWKS — never trust a decoded payload.** | base64-decode ≠ validate. Accepting `alg: none` is the Storm-0558 failure in Python. |
| 3 | **Token lifetime is a blast-radius control** (this realm: `exp` = 300 s). | A long `exp` restores session trust and widens the stolen/forged-token window. |
| 4 | **Scope to a single `aud` + minimal claims.** | Blocks cross-app replay; a 40-role JWT is VPN access re-packaged as JSON. |
| 5 | **Federation broker: the upstream group→role map IS the trust decision.** | Wrong map hands your authz to the upstream IdP; Golden SAML (T1606.002) forges that seam. |
| 6 | **The real handles:** realm `corp`, client `corp-app` / secret `corp-app-secret`, users `analyst` / `analyst123` and `admin` / `admin456`. | These are the exact strings you type; the module prose used placeholders. |
| 7 | **Two grants, opposite trust:** the **password grant** hands the *app* the user's password; **Authorization Code** sends it only to Keycloak. | ROPC is the shortcut (and OAuth 2.1-deprecated); the redirect flow is what real apps use. The `client_secret` proves the *app*, not the user. |

*(If you can explain all seven cold at the end — especially #1 and #2 — you've got the objective.)*

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
3. Two OAuth grants show up in this lab: one sends the user's password **through the application**,
   the other sends it **only to the IdP**. Name which is which — and say why the second is the
   default for a real app.

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
`realm_access.roles`, `aud`, and `exp`. Then paste the raw analyst token (grab it yourself in step 2, or
from the demo output) into [jwt.io](https://jwt.io/) and confirm the header names an **asymmetric**
algorithm (RS256), not `none` or an HMAC.

> **▸ On track if:** the demo banner reads *"Lab 02 — OIDC Token Demo: Corp realm"*, the analyst payload
> shows `realm_access.roles` containing **`analyst`**, `azp` is **`corp-app`**, and a single `aud` of
> **`corp-app`** (Step 4 calls this out — the token is audience-bound, not a catch-all), and the closing
> lines note the token **expires in 300 seconds**. Step 3 of the demo prints the JWKS **Key ID** and
> **Alg: RS256** — that public key is what your validator will fetch.

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

### Step 3 — Run the flow a real app uses (Authorization Code)

**Concept (30 sec):** Steps 1–2 used the **password grant** (`grant_type=password`) — the
*shortcut*: you handed the user's password straight to `curl` playing the client. Real apps must
**never** see the password. The **Authorization Code flow** is how they avoid it — the password
goes only to Keycloak, and the app gets back a one-time `code` it redeems, with its
`client_secret`, on a back channel. Watch where the password goes in each leg.

**Do it:** the callback app came up with `make up` — it's already serving at `http://localhost:3000`.
Walk the four legs.

1. **The redirect out.** Open `http://localhost:3000` and click **Log in with Keycloak**. The app
   builds an `/auth?response_type=code&client_id=corp-app&redirect_uri=…&scope=openid&state=…` URL
   and redirects your *browser* to Keycloak. The app never touches your credentials; `state` is a
   CSRF token it will re-check on the way back.
2. **Login at the IdP.** You land on the **real Keycloak login page** — note the URL is on `:8080`
   (Keycloak), not `:3000` (the app). Log in as **`analyst` / `analyst123`**. Your password went
   **to Keycloak, never to the app.** That is the whole difference from Steps 1–2.
3. **The redirect back.** Keycloak sends your browser to `http://localhost:3000/callback?code=…`.
   The app's page shows exactly what it received: a **`code`** and your `state` — and **no
   password**. That `code` is single-use, expires in ~60 s, and is **useless to anyone without
   `corp-app`'s `client_secret`.**
4. **The back-channel exchange.** Copy the pre-filled `curl` the page shows and run it. It POSTs
   `code` + `client_secret` + `redirect_uri` to the token endpoint and returns the tokens. This
   server-to-server call is where the secret proves the app — the browser never makes it.

Decode the `access_token` and compare it to your Step 2 analyst token: **same claims, same shape** —
nothing about validation changes, because a token is a token regardless of which grant minted it. (The
signature differs — it's a freshly minted token — but the validator you build in *Automate & own it*
accepts it exactly the same way.) What changed is that the app never saw the password. *That* is what
the redirect flow buys you.

> **▸ On track if:** the login page you typed into was served by Keycloak on `:8080`; the app's
> callback page showed a `code` but **no password**; and the exchange `curl` returned an
> `access_token` whose claims match your Step 2 analyst token. If the exchange returns
> `invalid_grant`, the code expired (>60 s) or was already spent — click **Log in** again for a
> fresh one.

### Step 4 — Find the blast-radius controls in the realm

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

### Step 5 — Reason about the two abuses: stolen token vs stolen key

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

### Step 6 — Verify the signature yourself (the gate that matters)

**Concept (30 sec):** Flight-card #1 + #2. Everything so far read the *easy* gates — decode the claims,
eyeball the `alg`, reason about `exp`/`aud`. **None of that is validation.** The load-bearing gate is the
one you haven't run: **verify the RS256 signature against the realm's public key.** A base64 decode
proves nothing — a forged `alg: none` token decodes to perfect-looking claims. This is the Storm-0558
line, so know exactly what "correct" is *before* you (or a model) write `validate-token.py` next.

**Do it (understand it here; build it in *Automate & own it*):** a real validator runs four gates, in
order. Softening or skipping any one is how a "validator" becomes a decoder:

1. **Algorithm — reject before any crypto.** Read the header `alg` and refuse anything that isn't
   `RS256`. This single check kills `alg: none` *and* the RS256→HS256 key-confusion trick. The fatal
   mistake is trusting the token's own `alg`; you **hard-code** the algorithm you accept.
2. **Key — fetch the realm's *public* key from JWKS**, selected by the token header's `kid` (the
   `…/openid-connect/certs` endpoint from Step 1's demo). You hold no shared secret — verification uses
   the public half of the realm's signing key.
3. **Signature — verify the RSA signature over `header.payload`.** One changed byte fails it. In Python
   that is `jwt.decode(token, public_key, algorithms=["RS256"], …)`; with the `step` CLI it's
   `step crypto jwt verify --alg RS256` — either way the `algorithms`/`--alg` you accept is **pinned by
   you, never read from the token**.
4. **Claims — enforce `exp`, `aud`, `iss`** (and require they are present), only *after* the signature
   verifies.

**Two ways to build this — pick one, but know the four gates either way.**

- **Python (`validate-token.py`).** You write the gates explicitly: read `alg`, fetch the JWKS key by
  `kid`, `jwt.decode(..., algorithms=["RS256"])`, then check the claims. More code — but every gate is
  visible on the page, so you can *see* exactly where a softened check would let a forgery through.
  Build it in *Automate & own it*.
- **`step` (smallstep CLI) — no Python.** One command enforces all four gates through flags:

  ```bash
  echo "$TOKEN" | step crypto jwt verify \
    --jwks <(curl -s http://localhost:8080/realms/corp/protocol/openid-connect/certs) \
    --iss http://localhost:8080/realms/corp --aud corp-app --alg RS256
  ```

  `--alg RS256` is gate 1 (the accepted algorithm pinned by *you*, not the token); `--jwks` is gates
  2–3 (fetch the realm's public key by `kid`, verify the signature); `--iss`/`--aud` — plus `exp`,
  checked automatically — is gate 4. It prints the decoded JWT and exits `0` on success, and exits
  **non-zero** on a bad signature or a failed claim. That non-zero exit is your rejection proof.

The tradeoff: `step` *hides* the gates behind flags — the faster path, but the weaker teacher. If you
take it, make sure you can still name what each flag enforces and why pinning `--alg` (rather than
trusting the token's own `alg`) is what defeats both `alg: none` and RS256→HS256 confusion. Install with
`brew install step`; see the [smallstep CLI docs](https://smallstep.com/docs/step-cli/).

> **▸ On track if:** you can name the four gates and say why pinning `algorithms=["RS256"]` (not the
> token's `alg`) is what defeats both `alg: none` and HMAC confusion. One thing worth knowing before you
> test it: the honest way to forge a *tampered* token is to **edit a claim and reuse the old signature**
> (e.g. self-grant `admin`) — that deterministically fails the signature gate. Flipping a random
> character is a weaker test: it usually corrupts the base64/JSON so the token is rejected as *malformed*
> before the signature is ever checked (and a flipped padding bit changes nothing at all).

---

## Prove the control (your finish line)

One check proves you built a **validator**, not a decoder. Run your validator — `validate-token.py`
(below), or the `step crypto jwt verify` one-liner from Step 6 — three times against your running realm
and *watch* the outcomes:

> 1. a **real** token minted in step 2 → **accepted**, claims printed;
> 2. a token with an **edited claim** (self-grant `admin`, reuse the original signature) → **rejected**
>    (the signature no longer covers the changed bytes — *this* is the gate that matters);
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
4. In the Authorization Code flow, your password reached exactly one party and the app received
   exactly one thing. Name both — and say what makes the `code` useless to a thief who does not
   have the `client_secret`.

Missed one? Re-run the step that built it, or pull the [validation-gates section](README.md#validation-is-a-chain-of-gates-not-a-base64-decode) — then re-answer.

---

## Deliverables

- **`oidc-analysis.md`** — containing: the decoded claims for **both** `analyst` and `admin` (keep the
  payload, redact the signature); which claims differ and the access decision each produces; your defense
  of the `accessTokenLifespan: 300` setting; the token-abuse scenario with your stolen-token mitigation
  **and** the stolen-signing-key contrast (step 5b); and the Okta federation paragraph (step 5c), labelled
  assessed-from-config.
  Add a short **Authorization Code walkthrough** — the four legs (redirect out, login at the IdP,
  redirect back with the `code`, back-channel exchange) and, for each grant, **where the user's
  password went**.
- **`validate-token.py`** — the working validator from *Automate & own it*, committed with it. (Took the
  no-Python route? Commit your `step`-based `verify.sh` here instead — either satisfies this deliverable.)

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

> **No-Python route (`step`).** If you'd rather not build a Python validator, wrap the `step crypto jwt
> verify` one-liner from Step 6 in a small `verify.sh` (mint the token with `curl`, pipe it into `step`
> with `--alg RS256 --jwks … --iss … --aud …`) and commit that as your validator instead. It still owes
> you the same proof: watched acceptance of a real token and *non-zero-exit rejection* of both a tampered
> token and an `alg: none` one. The point of the exercise isn't the language — it's that you can state,
> and demonstrate, which gate catches each forgery.

## Definition of done (`identity-control-plane` ✅)

- [ ] `make up` reports `Keycloak is ready.` and `make demo` prints decoded JWTs for analyst and admin
  plus the JWKS key (RS256).
- [ ] You have manually minted and decoded tokens for **both** users via `curl` and can list the claims
  that differ and the access decision each drives.
- [ ] You ran the **Authorization Code flow** in the browser (the callback app comes up with `make up`
  at `http://localhost:3000`), logged in on Keycloak's own page, and **redeemed the `code` by hand** —
  and can say where your password went in each grant.
- [ ] Your memo defends `accessTokenLifespan: 300`, contrasts a stolen token (bounded by `exp`/`aud`)
  with a stolen signing key (Storm-0558 / Golden SAML), and names what would have to leak from *this*
  realm for the key scenario to apply.
- [ ] The Okta federation paragraph names the group→role mapping as the trust decision and cites
  T1606.002.
- [ ] Your validator — `validate-token.py` **or** the `step`-based `verify.sh` — accepts a real token and
  you have **watched it reject** both a tampered token and an `alg: none` token.
- [ ] `oidc-analysis.md` + your validator are committed; you can explain all seven flight-card facts cold.

## Connects forward

- **Module 03 — Device Trust & Posture** binds *device* identity to the access decision alongside the
  user identity you just proved — the next layer of the ZT stack.
- **Module 05 — SASE** uses a cloud enforcement point that consumes OIDC identity claims from an upstream
  IdP in exactly this pattern (issuer URL + JWKS endpoint for validation).
- **Module 11 — Red-team your own ZT deployment** attacks the federation trust seam you reasoned about
  here: forge the identity assertion and see whether the design holds.

## Marketable proof

> "I can deploy an OIDC identity broker, walk a JWT token flow end-to-end — *both the password grant and the
> Authorization Code redirect flow, and why the redirect flow is the secure default* — including
> signature validation against the JWKS endpoint, and reason about token-abuse and signing-key-compromise
> blast radius and federation trust risk — the core skills for a Zero Trust identity architect or IAM
> engineer."

## Stretch

- **Audience enforcement.** The realm already ships a second client, `corp-api` (service-account only,
  60 s tokens). Show that a `corp-app` access token is *not* valid for a resource that expects the
  `corp-api` audience — `aud` enforcement that stops cross-app token replay.
- **Brute-force lockout.** The realm has `bruteForceProtected: true`. Script repeated bad-password logins
  for `analyst`, trigger the lockout, and document exactly what an attacker learns (or doesn't) from the
  error response.
- **Map to ATT&CK.** Tie your two abuse scenarios to **T1528** (Steal Application Access Token) and
  **T1606.002** (Golden SAML), and write one sentence on which realm setting is the control for each.
- **PKCE for public clients.** `corp-app` is a *confidential* client — it proves itself with
  `client_secret`. A **public** client (an SPA or mobile app) can't keep a secret. Add
  `code_challenge` / `code_verifier` (PKCE) to the Authorization Code request and explain what PKCE
  puts in the secret's place, and why that closes the code-interception gap for clients that can't
  hold a secret.
