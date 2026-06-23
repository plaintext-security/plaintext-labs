# Lab 06 — Identity-Aware Proxy with Pomerium

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate.** You stand up an identity-aware proxy, run it, and verify the thing that
actually makes it Zero Trust: the **deny path**. The deliverable is the *operating proxy + the proven
deny path* — not a writeup. No grader; you verify your own work against the observable success criteria
below. (Honor system: the committed config, notes, and regression test are the proof.)

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/06-identity-aware-access
make up      # start Pomerium + the whoami backend
make demo    # show the denied request, then the authenticated request
make shell   # drop into a shell for manual exploration
make down    # stop everything
```

The environment starts:
- **Pomerium** (all-in-one mode with a built-in mock IdP) on port 8443
- **whoami** — a tiny HTTP service that echoes the request headers it received, on an internal Docker
  network with **no published port**

The backend is unreachable except through Pomerium. `make demo` shows both the denial (no token) and
the successful flow (mock-IdP-signed JWT). The mock IdP issues tokens for `@example.com` addresses, so
no real IdP account is needed.

> **Authorization note:** Only test systems you own or have explicit written permission to test.
> Everything here runs locally in Docker — no external targets, no authorization needed. The
> header-forgery and bypass steps below are aimed *at your own lab proxy* to prove it holds.

## Scenario

An organization runs several internal tools — a compliance dashboard, a data-science notebook, a
legacy audit app — that IT currently protects with "VPN + firewall rule." The security team wants to
pilot identity-aware access: publish the tools with **no inbound ports** and require a valid
IdP-issued JWT on every request. You are standing up the proof-of-concept with Pomerium and a local
mock IdP before wiring real Okta — and, because a proxy is only as good as the failures it refuses,
you will deliberately try to forge identity and bypass the proxy to prove the design holds.

## Do

Build it, operate it, then attack your own deny path until you've proven it closed.

**Build & operate the proxy**
1. [ ] **Read the config before you start.** Open `data/config.yaml` and identify the three concerns:
   the `authenticate` service URL, the `routes`, and each route's `policy`. Which claim does the
   `allow` stanza check? Note that the route sets `pass_identity_headers: true` — that is what injects
   the signed assertion upstream.
2. [ ] `make demo` and read **every line** of output. There are two requests: the first is denied (no
   JWT), the second succeeds. In the successful one, find the `X-Pomerium-Jwt-Assertion` header in the
   whoami echo — that is the signed claim packet the backend would verify to know who the caller is.

**Verify the deny path at the packet level**
3. [ ] **Reproduce the denial manually.** From your host:
   ```bash
   curl -sk https://localhost:8443/ -o /dev/null -w "%{http_code}\n"
   ```
   You should get a redirect (302) or an access-denied response — **never a 200 from the backend**.
   Then confirm the backend has no escape hatch: `docker compose ps` shows whoami with no published
   port, and an attempt to reach it directly from the host fails. (Goal: prove every path in goes
   through the proxy — the precondition that makes the proxy's verdict the *only* way in.)

**Centerpiece — try to forge identity, confirm it's refused**
4. [ ] **Forge a client-supplied identity header.** The failure class behind CVE-2026-40575 is a
   backend (or proxy) that trusts a header a *client* can also set. Send a request with a hand-set
   identity header and watch what reaches whoami:
   ```bash
   curl -sk https://localhost:8443/ \
     -H "X-Pomerium-Jwt-Assertion: forged.jwt.value" \
     -H "X-Forwarded-User: admin@example.com"
   ```
   You should still be **denied** — Pomerium is the one that mints/overwrites the signed assertion, so
   a client-supplied value does not get the caller in. Inspect the whoami echo (when authenticated):
   does *your* forged header survive to the backend, or does Pomerium strip/overwrite it? Document the
   answer — it is the whole header-trust lesson.
5. [ ] **State the backend's rule in one sentence (the judgment).** In `notes.md`, write the rule a
   real upstream must follow: *trust the identity in `X-Pomerium-Jwt-Assertion` only after verifying
   its signature against Pomerium's JWKS (`/.well-known/pomerium/jwks.json`), plus `aud`/`iss`/`exp`;
   never trust a plain or client-supplied identity header.* Explain why a signed assertion is
   unforgeable without the proxy's private key while a plain header costs nothing to set.

**Tighten the policy and prove the stricter route denies**
6. [ ] **Add a second, stricter route.** In `data/config.yaml`, duplicate the route block to protect a
   second path/host and set its `allow` to require a claim the mock IdP does **not** issue (e.g.
   `groups: has: "finance-admins"`). `make down && make up`. Confirm the new route denies **even with a
   valid `@example.com` token**, while the original route still serves. (Goal: policy is per-route, and
   a valid identity is necessary but not sufficient — authorization is separate from authentication.)

**Map to production**
7. [ ] **Inspect the upstream headers** (`make shell`, then `curl` to `whoami` through Pomerium with a
   spoofed `X-Forwarded-For`): which headers does Pomerium rewrite vs. pass through, and which one
   carries the verified identity? Then write the production mapping in `notes.md`: which two fields in
   `config.yaml` change to wire real Okta, what you add to the Okta app settings, and — crucially — the
   one line you would put in the upstream app to verify the assertion (or the `trusted-proxy-ip` /
   no-bypass control that keeps the backend reachable only through the proxy).

## Success criteria — you're done when

- [ ] `make demo` shows a clearly labelled denied request followed by a successful authenticated request.
- [ ] You reproduced the denial with a manual `curl` (non-200) **and** confirmed whoami has no published
      port and cannot be reached directly — no bypass.
- [ ] A request carrying a **forged** `X-Pomerium-Jwt-Assertion` / `X-Forwarded-User` header is denied
      (or the forged header is stripped/overwritten before whoami), and you've documented which.
- [ ] You added a second route whose stricter policy denies even a valid token, while the original route
      still serves.
- [ ] `notes.md` states the backend's verify-the-signed-assertion rule and the production-Okta mapping.

## Deliverables

- `config.yaml` — your modified Pomerium config (the second, stricter route added).
- `notes.md` — the header-trust rule (verify the signed assertion; never trust a plain header), the
  forged-header finding, the header rewrite/pass-through observations, and the production-Okta mapping.
- `check-deny.sh` + the `make check` target (see below).

Commit all three. Lab artifacts (the TLS material Pomerium generates at runtime) stay out of commits —
they're in `.gitignore`.

## Automate & own it

**Required — this is the deny path turned into a regression test (the secondary Judgment-as-Code beat).**
Write `check-deny.sh` that:
1. Starts the stack (`docker compose up -d`) and waits for healthy.
2. Asserts the unauthenticated request to `/` is **NOT** a 200 (the backend is protected).
3. Asserts a request with a **forged** identity header (`X-Pomerium-Jwt-Assertion` / `X-Forwarded-User`)
   is **NOT** a 200 (identity is not client-settable).
4. Asserts whoami has **no published port** (e.g. `docker compose port whoami 80` returns nothing).
5. Exits 0 on all-pass, 1 on any failure, with a clear per-check message.

Have a model draft it; **you read every line** before trusting it — especially that each assertion
fails *closed* (a check that errors must count as a failure, not a silent pass). Wire it as a `make
check` target. This is your policy regression test: a config change that accidentally opens access — or
starts trusting a client header, or publishes the backend port — must turn `make check` red. That red
is the whole point; a green proxy you can't re-prove is a proxy you don't actually trust.

## AI acceleration

Paste the Pomerium claim-matching syntax and the mock IdP's token payload (from `make demo`) into a
model and ask it to generate the `policy` block for the new stricter route. Then refuse to trust the
allow path: test the **deny** path yourself — a token that should be rejected, the forged-header
request, the direct-to-backend attempt — because AI policy skews permissive and the only proof is a
request that fails. The transferable skill is not prompting for Rego/Pomerium policy; it's owning the
deny path well enough to encode it in `check-deny.sh`.

## Connects forward

The signed assertion Pomerium injects is the input that **OPA (module 08)** evaluates for fine-grained
authorization — chain Pomerium (coarse: "is this caller authenticated?") with OPA (fine: "is this
analyst allowed to export?"). The forged-header and bypass attacks you ran here are the warm-up for the
**Red-team-your-own-deployment** module (Type 10), which attacks the published, gated service end to
end. And the no-bypass / trust-only-the-proxy discipline is exactly what the **VPN → ZTNA migration**
(Type 12) must preserve as it shifts apps off the flat network one cohort at a time.

## Marketable proof

> "I stand up an identity-aware proxy with no inbound ports, enforce per-route policy against verified
> JWT claims, and I prove the deny path holds against the real failure class — a forged identity header
> and a direct-to-backend bypass — with a regression test that goes red the moment the backend stops
> trusting only the proxy's signed assertion."

## Stretch

- Replace the mock IdP with a real OIDC provider (GitHub OAuth works): set `idp_provider`, the client
  ID/secret in a `.env`, and confirm the same `make demo` flow works with real tokens.
- **Verify the assertion in the backend for real.** Swap whoami for a tiny app (a few lines of Python
  with `PyJWT`) that fetches Pomerium's JWKS, validates `X-Pomerium-Jwt-Assertion` (signature, `aud`,
  `iss`, `exp`), and returns 200 only on a valid assertion — then re-run the forged-header attack and
  watch it 401. This is the upstream half of the trust boundary, made concrete.
- Add mTLS between Pomerium and the backend (`tls_upstream` on the route + a self-signed client cert)
  so even a proxy-bypass attempt requires the right client certificate.
