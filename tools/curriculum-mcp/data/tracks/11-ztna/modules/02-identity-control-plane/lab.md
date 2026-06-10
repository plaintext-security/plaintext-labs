# Lab 02 — Identity as the Control Plane: Keycloak + OIDC

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** with a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/02-identity-control-plane
make up        # start Keycloak with the Meridian realm pre-loaded
make demo      # show the full OIDC flow: get a token, decode it, inspect claims
make down      # stop when done
```

Keycloak starts on `http://localhost:8080`. The admin console is at
`http://localhost:8080/admin` (credentials: `admin` / `admin` — local dev only, never production).
The Meridian realm is imported automatically from `data/meridian-realm.json` on startup.

> Everything runs locally. No external services are contacted. No authorization issues.

## Scenario

Meridian's identity infrastructure is fragmented: AD Kerberos for on-prem apps, Okta for ~200
users, and LDAP binds for legacy systems. The security team wants to consolidate behind a proper
OIDC identity broker — one issuer, per-application access tokens, short-lived JWTs, and a clear
federation path to bring Okta users in without a second login. You'll stand up Keycloak as that
broker, walk the OIDC flow manually, and reason about how the federated trust would work in
production.

## Do

1. [ ] Run `make up` and wait for Keycloak to be ready. Then run `make demo` and read the full
   output — it will obtain a JWT for the `analyst` user and print the decoded claims. Before doing
   anything else, paste the raw token into [jwt.io](https://jwt.io/) and locate: `sub`, `aud`,
   `realm_access.roles`, and `exp`. How long until it expires?

2. [ ] **Walk the token flow manually.** Using `curl`, authenticate as the `analyst` user against
   the `meridian` realm and obtain a token yourself:
   ```bash
   curl -s -X POST http://localhost:8080/realms/meridian/protocol/openid-connect/token \
     -d "grant_type=password&client_id=meridian-app&client_secret=<secret>&username=analyst&password=analyst123&scope=openid" \
     | python3 -m json.tool
   ```
   Decode the `access_token` field with `jwt decode <token>` (or `python3 -c "import sys,base64,json; p=sys.argv[1].split('.')[1]; print(json.dumps(json.loads(base64.urlsafe_b64decode(p+'==').decode()),indent=2))" <token>`).
   List the claims present and note which ones would be used in an access decision.

3. [ ] **Compare analyst vs. admin.** Repeat the curl command for the `admin` user. Which claims
   differ? What roles does `admin` carry that `analyst` does not? This is the claim-based access
   control model in action: the application inspects `realm_access.roles`, not a network zone.

4. [ ] **Inspect the realm configuration** in the Keycloak admin console
   (`http://localhost:8080/admin`). Navigate to: Realm Settings → Tokens. Note the Access Token
   Lifespan. Is it consistent with ZT discipline (short-lived = good)? Then navigate to Clients →
   `meridian-app` → Scope. What scopes is this client allowed to request? Is there any scope that
   could carry more privilege than needed?

5. [ ] **Reason about token abuse.** If an attacker phishes the analyst's credentials and gets the
   JWT, what can they do with it? For how long? What would a `aud` (audience) restriction prevent?
   Write a short paragraph in your deliverable explaining one control that would limit blast radius
   on a stolen token.

6. [ ] **Federation exercise (prose).** Open `data/meridian-realm.json` and find the
   `identityProviders` array. It's currently empty. Write a paragraph in your deliverable
   describing what you would add to federate Okta as an upstream IdP via OIDC: what fields you'd
   configure (`authorizationUrl`, `tokenUrl`, `clientId`, `clientSecret`), what attribute mapper
   you'd add to translate Okta's `groups` claim to Keycloak roles, and what the trust risk is
   (Okta's group membership becomes your application's authorization — if the Okta mapping is
   wrong, so is your access decision).

## Success criteria — you're done when

- [ ] `make demo` runs cleanly and outputs a decoded JWT with the correct Meridian realm claims.
- [ ] You have manually obtained and decoded tokens for both `analyst` and `admin` users via `curl`.
- [ ] You can list the specific claims that differ between the two users and explain what access
  decision each would produce.
- [ ] Your deliverable addresses token lifetime, audience restriction, and the federation mapping risk.

## Deliverables

`oidc-analysis.md` — document containing:
- The decoded claims for both `analyst` and `admin` users (redact the signature, keep the payload)
- Your assessment of the realm's token lifetime setting against ZT discipline
- The token abuse scenario and your proposed mitigation
- The federation configuration paragraph (step 6)

## Automate & own it

**Required.** Write a Python script (`validate-token.py`) that:
1. Takes a Keycloak token URL and user credentials as arguments
2. Obtains a JWT via the Resource Owner Password Grant
3. Validates the token's signature against the realm's public key (fetch it from the JWKS endpoint:
   `http://localhost:8080/realms/meridian/protocol/openid-connect/certs`)
4. Prints the claims and flags if the token is within 60 seconds of expiry

Have a model draft this; **you review every line** — especially the signature validation logic. A
script that accepts an unsigned token (algorithm `none`) or skips signature verification is not a
token validator, it's an exploit. Verify it rejects a tampered token before committing.

## AI acceleration

Models generate OIDC `curl` flows and Python JWT validation code accurately. The risk is that they
produce code that skips signature validation ("just decode the base64 payload") or accepts weak
algorithms. Explicitly tell the model: "validate the signature against the JWKS endpoint; reject
tokens with alg:none." Then test it with a base64-modified token to confirm rejection.

## Connects forward

- Module 03 binds device identity to access decisions alongside user identity — the next layer of
  the ZT stack.
- Module 05 uses Cloudflare Access as the enforcement point, which consumes OIDC identity claims
  from an upstream IdP in exactly this pattern (issuer URL + JWKS endpoint for validation).

## Marketable proof

> "I can deploy an OIDC identity broker, walk a JWT token flow end-to-end including signature
> validation, and reason about token abuse scenarios and federation trust risks — the core skills
> for a ZT identity architect or IAM engineer."

## Stretch

- Configure a second Keycloak client (`meridian-api`) with a different scope and audience, and
  demonstrate that the `analyst` access token is rejected by the API client (audience mismatch).
  This is the `aud` claim enforcement that prevents token replay across applications.
- Enable Keycloak's Brute Force Protection on the `meridian` realm and write a test that triggers
  the lockout, then document what an attacker learns (or doesn't) from the error response.
