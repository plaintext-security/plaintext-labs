# Lab 02 — Identity as the Control Plane: Keycloak + OIDC

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate.** You stand up a real OIDC identity provider, run the full token flow
through it, and walk away with a running IdP plus a token you minted and *validated against its signing
key* — the working system is the point, not a write-up about it.

## Setup

This is a **reference lab** with a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/02-identity-control-plane
make up        # start Keycloak with the lab realm pre-loaded
make demo      # show the full OIDC flow: get a token, decode it, inspect claims
make down      # stop when done
```

Keycloak starts on `http://localhost:8080`. The admin console is at `http://localhost:8080/admin`
(credentials: `admin` / `admin` — local dev only, never production). The lab realm is imported
automatically from `data/realm.json` on startup.

> Everything runs locally. No external services are contacted. No authorization issues.

## Scenario

An organization's identity infrastructure is fragmented: AD Kerberos for on-prem apps, Okta for ~200
users, and LDAP binds for legacy systems. The security team wants to consolidate behind a proper OIDC
identity broker — one issuer, per-application access tokens, short-lived JWTs, and a clear federation
path to bring the Okta users in without a second login. You will stand up Keycloak as that broker, walk
the OIDC flow manually, and reason about how the federated trust would work in production — keeping one
eye on the question Storm-0558 made unforgettable: *what is the blast radius if this IdP's signing key
or an issued token leaks?*

## Do — build it, then operate it

**Build & run the IdP**

1. [ ] Run `make up` and wait for Keycloak to be ready, then `make demo` and read the full output — it
   obtains a JWT for the `analyst` user and prints the decoded claims. Before anything else, paste the
   raw token into [jwt.io](https://jwt.io/) and locate `sub`, `aud`, `realm_access.roles`, and `exp`.
   How long until it expires?

2. [ ] **Walk the token flow manually.** With `curl`, authenticate as the `analyst` user against the
   lab realm and obtain a token yourself:
   ```bash
   curl -s -X POST http://localhost:8080/realms/ztna-lab/protocol/openid-connect/token \
     -d "grant_type=password&client_id=ztna-app&client_secret=<secret>&username=analyst&password=analyst123&scope=openid" \
     | python3 -m json.tool
   ```
   Decode the `access_token` field with `jwt decode <token>` (or
   `python3 -c "import sys,base64,json; p=sys.argv[1].split('.')[1]; print(json.dumps(json.loads(base64.urlsafe_b64decode(p+'==').decode()),indent=2))" <token>`).
   List the claims present and note which ones drive an access decision.

3. [ ] **Compare `analyst` vs. `admin`.** Repeat the curl for the `admin` user. Which claims differ?
   What roles does `admin` carry that `analyst` does not? This is claim-based access control in action —
   the application inspects `realm_access.roles`, not a network zone.

**Operate it — inspect the controls that bound blast radius**

4. [ ] **Inspect the realm configuration** in the admin console (`http://localhost:8080/admin`).
   Realm Settings → Tokens: note the **Access Token Lifespan** — is it consistent with ZT discipline
   (short-lived = good)? Then Clients → `ztna-app` → Scope: what scopes may this client request, and is
   any scope carrying more privilege than the app needs?

5. [ ] **Reason about token abuse.** If an attacker phishes the analyst's credentials and steals the
   JWT, what can they do, and for how long? What would an `aud` (audience) restriction prevent?
   Now raise the stakes one level: in **Storm-0558** the attacker didn't steal a *token*, they stole the
   *signing key* and forged tokens at will. In your deliverable, write a short paragraph on (a) one
   control that limits blast radius on a **stolen token** (short `exp`, single `aud`) and (b) why a
   **stolen signing key** is categorically worse — and what would have to leak from *this* Keycloak
   realm for that scenario to apply.

6. [ ] **Federation exercise (assessed from config, not demonstrated).** Open `data/realm.json` and
   find the `identityProviders` array — it's currently empty. In your deliverable, describe what you
   would add to federate Okta as an upstream OIDC IdP: the fields you'd configure (`authorizationUrl`,
   `tokenUrl`, `clientId`, `clientSecret`), the attribute mapper that translates Okta's `groups` claim
   to Keycloak roles, and the trust risk (Okta group membership becomes *your* app's authorization — if
   the mapping is wrong, so is every access decision; this is the seam Golden SAML / T1606.002 abuses).
   Label this clearly as a config-level design, not something you stood up.

## Success criteria — you're done when (self-checked, honor system)

- [ ] `make demo` runs cleanly and outputs a decoded JWT with the correct lab-realm claims.
- [ ] You have manually obtained and decoded tokens for **both** `analyst` and `admin` via `curl`.
- [ ] You can list the specific claims that differ between the two users and the access decision each produces.
- [ ] `validate-token.py` (below) runs, validates a real token's signature against the JWKS endpoint,
  and **rejects a tampered token and an `alg: none` token** — you have observed both rejections yourself.
- [ ] Your deliverable addresses token lifetime, `aud` restriction, the stolen-token-vs-stolen-key
  distinction, and the federation mapping risk.

## Deliverables

`oidc-analysis.md` — containing:
- The decoded claims for both `analyst` and `admin` (redact the signature, keep the payload).
- Your assessment of the realm's token-lifetime setting against ZT discipline.
- The token-abuse scenario, your stolen-token mitigation, **and** the stolen-signing-key contrast (step 5).
- The federation configuration paragraph (step 6), labelled as assessed-from-config.

Plus the working artifact below. (Lab artifacts — raw tokens, the realm export, keys — stay out of commits.)

## Automate & own it

**Required.** Write `validate-token.py` that:
1. Takes a Keycloak token URL and user credentials as arguments.
2. Obtains a JWT via the Resource Owner Password Grant.
3. **Validates the token's signature** against the realm's public key, fetched from the JWKS endpoint
   (`http://localhost:8080/realms/ztna-lab/protocol/openid-connect/certs`).
4. Prints the claims and flags if the token is within 60 seconds of expiry.

Have a model draft it; **you review every line** — especially the signature path. A script that accepts
an unsigned token (`alg: none`) or skips verification is not a validator, it's the Storm-0558 failure
mode in miniature. **Before you commit, prove it both ways:** confirm it accepts a real token and
*rejects* a base64-tampered one and an `alg: none` one. That observed rejection is your self-check —
there is no grader here; the working, proven script is the proof.

## AI acceleration

Models generate OIDC `curl` flows and JWT-validation code accurately — and the failure mode is specific
and dangerous: they produce "validators" that decode the base64 payload without checking the signature,
or that accept weak/`none` algorithms. Tell the model explicitly: *"validate the signature against the
JWKS endpoint; reject `alg: none`."* Then test it with a base64-modified token to confirm rejection. The
whole posture of this module lives in that one test: AI drafts the validator, you prove it actually
validates, and only then do you own it.

## Connects forward

- Module 03 binds **device** identity to access decisions alongside user identity — the next layer of the ZT stack.
- Module 05 (SASE) uses Cloudflare Access as the enforcement point, consuming OIDC identity claims from an upstream IdP in exactly this pattern (issuer URL + JWKS endpoint for validation).
- The federation trust mapping you reasoned about here is the seam the Phase-3 *red-team-your-own-deployment* module attacks (forge the proxy's identity assertion and see if the design holds).

## Marketable proof

> "I can deploy an OIDC identity broker, walk a JWT token flow end-to-end *including signature
> validation against the JWKS endpoint*, and reason about token-abuse and signing-key-compromise blast
> radius and federation trust risk — the core skills for a ZT identity architect or IAM engineer."

## Stretch

- Configure a second Keycloak client (`ztna-api`) with a different scope and audience, and show that the
  `analyst` access token is **rejected** by the API client (audience mismatch) — `aud` enforcement that
  prevents token replay across applications.
- Enable Keycloak's Brute Force Protection on the realm, write a test that triggers the lockout, and
  document what an attacker learns (or doesn't) from the error response.
