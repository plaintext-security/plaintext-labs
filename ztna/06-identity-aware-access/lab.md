# Lab 06 — Identity-Aware Proxy with Pomerium

*Hands-on lab · [← Back to the module concept](README.md)*


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
- **whoami** — a tiny HTTP service that echoes request headers, running on an internal Docker network with no published port

The backend is unreachable except through Pomerium. `make demo` shows both the denial (no token) and the successful flow (mock-IdP-signed JWT).

> Only test systems you own or have explicit written permission to test. Everything here runs locally in Docker — no external targets, no authorization needed.

## Scenario

Meridian Financial is running several internal tools — a compliance dashboard, a data-science notebook, and a legacy audit app — that IT currently protects with "VPN + firewall rule." The security team wants to pilot identity-aware access: publish the tools with **no inbound ports** and require a valid Okta-issued JWT on every request. You are standing up the proof-of-concept using Pomerium with a local mock IdP before connecting real Okta.

## Do

1. [ ] **Read the config before you start.** Open `data/config.yaml` and identify the three sections: `authenticate`, `routes`, and `policy`. Which email or group claim does the `allow` stanza check? What path does an unauthenticated user land on?

2. [ ] `make demo` and read every line of output. There are two requests: the first is denied (no JWT), the second succeeds. For the successful one, find the `X-Pomerium-Jwt-Assertion` header in the whoami output — this is the signed claim packet the backend would use to know who the caller is.

3. [ ] **Simulate a denied request manually.** From your host:
   ```bash
   curl -sk https://localhost:8443/ -o /dev/null -w "%{http_code}"
   ```
   You should get a redirect (302) or an access-denied response, never a 200 from the backend. Confirm the backend container is not reachable directly (no published port for whoami).

4. [ ] **Edit policy to add a second route.** In `data/config.yaml`, duplicate the existing route block and change it to protect path `/admin`. Set the `allow` policy to require a claim that the mock IdP does *not* issue (e.g. `groups: contains: "finance-admins"`). Restart with `make down && make up`. Confirm that `/admin` now returns a denial even with a valid token, while the original path still works.

5. [ ] **Inspect the upstream headers.** `make shell` and run:
   ```bash
   curl -sk https://pomerium:8443/ -H "X-Forwarded-For: 10.0.0.1"
   ```
   Look at what the whoami service receives. Does `X-Forwarded-For` pass through as-is, or does Pomerium rewrite it? What header carries the user identity? Document your findings.

6. [ ] **Map this to production.** Write a short note (add it to your deliverable) explaining what you would change to connect real Okta: which two fields in `config.yaml` change, and what you would add to your Okta application settings.

## Success criteria — you're done when

- [ ] `make demo` shows a clearly labelled denied request followed by a successful authenticated request.
- [ ] You can reproduce the denial with a manual `curl` and confirm the backend has no published port.
- [ ] You've added a second route with a stricter policy and confirmed it denies even a valid token.
- [ ] You've identified and documented the identity-injection headers the backend receives.

## Deliverables

- `config.yaml` — your modified Pomerium config with the second route and stricter policy
- `notes.md` — the header inspection findings and the production-Okta mapping notes

Commit both. Lab artifacts (TLS material generated at runtime) stay out of commits — they're in `.gitignore`.

## Automate & own it

**Required.** Write a shell script `check-policy.sh` that:
1. Starts the stack (`docker compose up -d`)
2. Makes an unauthenticated request to `/` and asserts it is NOT a 200 (the backend must be protected)
3. Exits 0 on pass, 1 on failure, with a clear message

Have a model draft it; **you read every line** before trusting it. Then wire it as a `make check` target. This is the minimal "policy regression test" — a script that proves your proxy still denies the unauthenticated path. A config change that accidentally opens access should fail this check.

## AI acceleration

Paste the Pomerium docs' claim-matching syntax and your IdP's JWT payload (or the mock IdP's output from `make demo`) into a model and ask it to generate the `policy` block for a new route. Then test the deny path yourself — AI policy is frequently too permissive, and the only way to know is to send a request that should fail.

## Connects forward

The identity headers Pomerium injects — especially the signed JWT — are the inputs that OPA (module 08) evaluates to make fine-grained authorization decisions. You can chain Pomerium (coarse "is this user authenticated?") with OPA (fine "is this analyst allowed to export data?") for layered policy.

## Marketable proof

> "I can stand up an identity-aware proxy with no inbound ports, enforce per-route policy against JWT claims, and write a regression test that proves the backend is unreachable without a valid token."

## Stretch

- Replace the mock IdP config with a real OIDC provider (GitHub OAuth works; enable it in Pomerium's `authenticate` section and update the client ID/secret in a `.env` file). Confirm the same `make demo` flow works with real tokens.
- Add mTLS between Pomerium and the backend: configure `tls_upstream` in the route and issue a self-signed cert for the whoami container. Now even a proxy bypass attempt requires the right client certificate.
