# Lab 06 — Identity-Aware Proxy with Pomerium: prove the deny path holds

> **Hands-on lab.** Environment: `plaintext-labs/ztna/06-identity-aware-access`.
> Objective: **stand up an identity-aware proxy with no inbound port on the origin, then prove the deny
> path refuses a forged identity header and a direct-to-backend bypass.** Target: **~90 min**, one
> finish line. This is a **container lab** — Pomerium + a whoami backend under Docker.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The origin has NO inbound port.** | This is the property that negates a pre-auth VPN RCE (Ivanti CVE-2023-46805/21887, Pulse CVE-2019-11510) — no unauthenticated surface to attack. |
| 2 | **Every request needs a valid signed token.** | No token = 302/drop, **not a 200**. The unit of access is the request, not a session. |
| 3 | **Two ways the deny path fails: forged header + bypass.** | They're duals of one rule — break either and the proxy is theater. |
| 4 | **Trust only the *signed* assertion** (`X-Pomerium-Jwt-Assertion`, verified vs JWKS). | A plain `X-Forwarded-User` header is free to forge; a signed one needs the proxy's private key. |
| 5 | **Policy is per-route; authn ≠ authz.** | A valid `@example.com` token is necessary but not sufficient — a stricter route still denies it. |
| 6 | **The deny path is the deliverable.** | Encode it in `check-deny.sh` / `make check` so a config change can't silently reopen access. |

*(If you can explain all six cold at the end — especially #1 and #4 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core-idea section](README.md#the-core-idea), the
> [no-inbound-port / case-study seam](README.md#the-case-study-seam-a-pre-auth-vpn-rce-that-no-inbound-ports-negates),
> and the [deny-path conditions](README.md#where-this-still-fails-the-deny-path-only-holds-under-two-conditions).

---

## Warm-up — answer before you start the stack (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. The Ivanti/Pulse VPN appliances were owned by *unauthenticated* attackers with no credential. Name the
   one property of the identity-aware model that removes that entire class of attack. (Hint: it's about
   what the origin listens on.)
2. A backend reads `X-Forwarded-User: admin@example.com` and trusts it. Why is that catastrophic, and
   what would it have to check *instead* before believing any identity?

---

## Setup

This is a **reference lab** — a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/06-identity-aware-access
make up      # start Pomerium + the whoami backend
make demo    # show the denied request, then the authenticated flow + no-port check
make shell   # drop into the Pomerium container for manual exploration
make check   # policy smoke-test: unauthenticated request must NOT be a 200
make down    # stop everything
```

The environment starts **Pomerium** (all-in-one, built-in mock IdP) on `https://localhost:8443`, and
**whoami** (a tiny service that echoes the request headers it received) on an internal Docker network
with **no published port**. The mock IdP issues tokens for `@example.com` addresses, so no real IdP
account is needed. Pomerium auto-generates a self-signed cert — clients use `-k` / `--insecure`.

> **▸ On track if:** `make demo` prints `== 1. Unauthenticated request — no JWT ==`, an
> `Expected: 302 (redirect to IdP login) — NOT a 200`, and ends with
> `PASS: whoami has no published port — only reachable via Pomerium.` The file you reason *about* is
> **`data/config.yaml`** — the `authenticate_service_url`, the `routes`, and each route's `policy`.

> **Authorization note.** Everything runs locally in Docker — no external targets, no authorization
> needed. The header-forgery and bypass steps below are aimed *at your own lab proxy* to prove it holds.
> The binding rule still stands for anything else: only test systems you own or have explicit written
> permission to test. Identity-aware proxies touch real access — point them only at your own resources.

---

## Build it — read a little, do a little

### Step 1 — Read the config, then run the demo

**Concept (30 sec):** Flight-card #2. A route wires an external URL Pomerium listens on to an internal
upstream. `pass_identity_headers: true` is what injects the signed assertion upstream; the `allow`
stanza is the policy the token is judged against.

**Do it:** open `data/config.yaml` and name the three concerns — `authenticate_service_url`, `routes`,
and each route's `policy`. Which claim does the `allow` stanza check? Then `make up && make demo` and
read **every line**.

> **▸ On track if:** you can point at the `email: ends_with: "@example.com"` allow rule and the
> `pass_identity_headers: true` line, and `make demo` shows the unauthenticated request expected as a
> **302, not a 200**, followed by the `PASS: whoami has no published port` line.

### Step 2 — Prove the origin has no inbound port (the case-study seam)

**Concept (30 sec):** Flight-card #1. This is the property that negates the Ivanti/Pulse pre-auth RCE —
there is no unauthenticated internet-facing service to exploit because the origin listens only on the
internal network the proxy can reach.

**Do it:** confirm whoami has no published port, and that you cannot reach it around the proxy:

```bash
docker compose ps                 # whoami row shows NO 0.0.0.0:->80 mapping
docker compose port whoami 80     # prints nothing — no host binding
```

Then reproduce the denial from your host against the actual route (Pomerium routes by Host):

```bash
curl -sk --resolve whoami.localhost.pomerium.io:8443:127.0.0.1 \
  https://whoami.localhost.pomerium.io:8443/ -o /dev/null -w "%{http_code}\n"
```

> **▸ On track if:** `docker compose port whoami 80` prints nothing, and the `curl` returns a **302 (or
> other non-200)** — never a 200 from whoami. If you get a 200, the backend is exposed and the deny
> path is already broken.

### Step 3 — Forge a client-supplied identity header, confirm it's refused (centerpiece)

**Concept (30 sec):** Flight-card #4. The failure class behind CVE-2026-40575 is a proxy/backend that
trusts a header a *client* can also set. Pomerium mints/overwrites the signed assertion itself, so a
client-supplied value must not get you in.

**Do it:** send a hand-set identity header and watch what happens:

```bash
curl -sk --resolve whoami.localhost.pomerium.io:8443:127.0.0.1 \
  https://whoami.localhost.pomerium.io:8443/ \
  -H "X-Pomerium-Jwt-Assertion: forged.jwt.value" \
  -H "X-Forwarded-User: admin@example.com" \
  -o /dev/null -w "%{http_code}\n"
```

You should still be **denied**. Then, once you complete a real mock-IdP login in a browser (see the
`make demo` notes — add `127.0.0.1 whoami.localhost.pomerium.io` to `/etc/hosts`, log in as
`user@example.com`), inspect the whoami header echo: does *your* forged header survive to the backend,
or does Pomerium strip/overwrite it? Document the answer in `notes.md` — that is the whole header-trust
lesson.

> **▸ On track if:** the forged-header request is **non-200**, and you can state in one sentence the
> rule a real upstream must follow: *trust `X-Pomerium-Jwt-Assertion` only after verifying its signature
> against Pomerium's JWKS (`/.well-known/pomerium/jwks.json`) plus `aud`/`iss`/`exp` — never a plain,
> client-supplied identity header.*

### Step 4 — Add a stricter route; prove authn ≠ authz

**Concept (30 sec):** Flight-card #5. Policy is per-route. A valid identity is necessary but not
sufficient — authorization is separate from authentication.

**Do it:** in `data/config.yaml`, duplicate the route block to protect a second host (e.g.
`admin.localhost.pomerium.io`) and set its `allow` to require a claim the mock IdP does **not** issue —
`groups: has: "finance-admins"`. Then `make down && make up`. Confirm the new route denies **even with a
valid `@example.com` token**, while the original route still serves.

> **▸ On track if:** the original route still authenticates a real browser login, but the new
> `admin.*` route denies the same valid token — the difference is authorization, not identity.

### Step 5 — Map to production

**Concept (30 sec):** The lab's mock IdP stands in for real Okta. Two `config.yaml` fields change; the
upstream must verify the assertion or be reachable only through the proxy.

**Do it:** in `notes.md`, write the production mapping — which two fields in `config.yaml` change to
wire real Okta (`idp_provider`, `idp_client_id`/`idp_client_secret`), what you add to the Okta app
settings, and the **one line** you'd put in the upstream to verify the assertion (or the
`trusted-proxy-ip` / no-bypass control that keeps the backend reachable only through the proxy).

> **▸ On track if:** `notes.md` names the exact Okta wiring fields *and* the upstream verify-or-no-bypass
> control — not just "use Okta."

---

## Prove the control (your finish line)

Run the one check that proves the deny path is closed — the denied-and-no-bypass pair that makes this a
Zero-Trust deployment rather than a reverse proxy:

```bash
make check                        # asserts the unauthenticated request is NOT a 200
docker compose port whoami 80     # prints nothing — no inbound port on the origin
```

**The proof:** `make check` must print `PASS: got HTTP <non-200> — backend is protected (not a 200).`
**and** `docker compose port whoami 80` must return empty. Together they show both halves of the rule:
the origin is unreachable except through the proxy (no bypass — the same property that negates the
Ivanti/Pulse pre-auth RCE), and an unauthenticated request never touches it. *If `make check` ever
prints a 200, the deny path is open and everything downstream is wrong — fix it before you commit.*

---

## Recall check — close the docs, answer from memory (3 min)

1. Which single property of the identity-aware model removes the pre-auth VPN-appliance RCE class, and why?
2. What must an upstream verify on `X-Pomerium-Jwt-Assertion` before trusting the identity inside it — and why is a plain `X-Forwarded-User` header worthless as proof?
3. Name the two ways the deny path fails, and why they're duals of the same rule.

Missed one? Re-run the step that built it, or pull the [deny-path section](README.md#where-this-still-fails-the-deny-path-only-holds-under-two-conditions) — then re-answer.

---

## Deliverables

- **`config.yaml`** — your modified Pomerium config (the second, stricter route added).
- **`notes.md`** — the header-trust rule (verify the signed assertion; never trust a plain header), the
  forged-header finding (did it survive to whoami?), and the production-Okta mapping.
- **`check-deny.sh`** + the `make check` target (see below).

Commit all three. Lab artifacts (the TLS material Pomerium generates at runtime) stay out of commits —
they're in `.gitignore`.

## Automate & own it

**Required — this is the deny path turned into a regression test (the secondary Judgment-as-Code beat).**
Extend the shipped `make check` smoke-test into a full `check-deny.sh` that:

1. Starts the stack (`docker compose up -d`) and waits for Pomerium healthy.
2. Asserts the unauthenticated request to the route is **NOT** a 200 (the backend is protected).
3. Asserts a request with a **forged** identity header (`X-Pomerium-Jwt-Assertion` / `X-Forwarded-User`)
   is **NOT** a 200 (identity is not client-settable).
4. Asserts whoami has **no published port** (`docker compose port whoami 80` returns nothing).
5. Exits 0 on all-pass, 1 on any failure, with a clear per-check message.

Have a model draft it; **you read every line** — especially that each assertion fails *closed* (a check
that errors counts as a failure, not a silent pass). Wire it as `make check`. This is your policy
regression test: a config change that accidentally opens access — starts trusting a client header, or
publishes the backend port — must turn `make check` red. That red is the whole point; a green proxy you
can't re-prove is a proxy you don't actually trust.

## Definition of done (`identity-aware-access` ✅)

- [ ] `make demo` shows a labelled denied (302) request and the `PASS: whoami has no published port` line.
- [ ] You reproduced the denial with a manual `curl` (non-200) **and** confirmed `docker compose port whoami 80` is empty — no bypass.
- [ ] A request carrying a **forged** `X-Pomerium-Jwt-Assertion` / `X-Forwarded-User` header is denied (or the forged header is stripped before whoami), and you documented which.
- [ ] A second, stricter route denies even a valid `@example.com` token while the original still serves.
- [ ] `notes.md` states the verify-the-signed-assertion rule and the production-Okta mapping.
- [ ] `check-deny.sh` (wired as `make check`) goes **red** on an unauthenticated 200, a trusted forged header, or a published backend port; `config.yaml` + `notes.md` + `check-deny.sh` are committed.

## Connects forward

- The signed assertion Pomerium injects is the input **OPA (Module 08)** evaluates for fine-grained
  authorization — chain Pomerium (coarse: "is this caller authenticated?") with OPA (fine: "is this
  analyst allowed to export?").
- The forged-header and bypass attacks here are the warm-up for the **Red-team-your-own-deployment**
  module (Type 10), which attacks the published, gated service end to end.
- The no-bypass / trust-only-the-proxy discipline is exactly what the **VPN → ZTNA migration** (Module 10)
  must preserve as it shifts apps off the flat network one cohort at a time — retiring the very
  Ivanti/Pulse-style appliance this module indicts.

## Marketable proof

> "I stand up an identity-aware proxy with no inbound ports on the origin, enforce per-route policy
> against verified JWT claims, and I prove the deny path holds against the real failure class — a forged
> identity header and a direct-to-backend bypass — with a regression test that goes red the moment the
> backend stops trusting only the proxy's signed assertion. I can explain why that architecture negates
> the pre-auth VPN-appliance RCEs (Ivanti, Pulse Secure) that a perimeter VPN can't."

## Stretch

- Replace the mock IdP with a real OIDC provider (GitHub OAuth works): set `idp_provider`, the client
  ID/secret in a `.env`, and confirm the same `make demo` flow works with real tokens.
- **Verify the assertion in the backend for real.** Swap whoami for a tiny Python app (`PyJWT`) that
  fetches Pomerium's JWKS, validates `X-Pomerium-Jwt-Assertion` (signature, `aud`, `iss`, `exp`), and
  returns 200 only on a valid assertion — then re-run the forged-header attack and watch it 401. This is
  the upstream half of the trust boundary, made concrete.
- Add mTLS between Pomerium and the backend (`tls_upstream` on the route + a self-signed client cert)
  so even a bypass attempt requires the right client certificate.
