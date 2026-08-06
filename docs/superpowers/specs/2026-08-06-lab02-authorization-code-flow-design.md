# Lab 02 — Add the Authorization Code flow (the flow a real app uses)

**Date:** 2026-08-06
**Lab:** `ztna/02-identity-control-plane`
**Status:** Design approved, pending spec review

---

## Problem

Lab 02 currently walks the OIDC token flow using **only** the Resource Owner Password
Credentials grant (`grant_type=password`, aka ROPC / direct access grant). Every step —
`make demo` and the by-hand `curl` in Step 2 — hands the user's password directly to `curl`
acting as the client. The lab never names this as a shortcut, and never shows the flow a real
application actually uses.

The consequence: a learner finishes Lab 02 having only ever performed the **anti-pattern**. The
"full picture of identity" is missing precisely the half that makes OAuth OAuth — the redirect
handshake where **the password goes only to the IdP and the application never sees it**. The
recurring question the lab should answer ("why is a `client_secret` bundled with a
username/password, and isn't handing the app the password backwards?") is left unanswered.

## Goal

Add the **Authorization Code flow** to Lab 02 so the learner experiences, in detail, the flow a
real confidential client uses — and can contrast it with the ROPC shortcut they already ran. The
learner should come away able to state **where the password goes in each grant** and **what the
`client_secret` actually proves**.

Non-goals: PKCE in the core path (confidential client — offered as a stretch); a production-grade
web app; a second container; any change to the realm export.

## Key facts (already true in the repo — no change needed)

- `corp-app` already has `standardFlowEnabled: true` and
  `redirectUris: ['http://localhost:3000/*']`. The realm already supports the code flow; there is
  simply no app catching the redirect today.
- `corp-app` is a **confidential** client (`publicClient: false`) with `corp-app-secret`.
- The lab already depends on `python3` (used throughout the Makefile), so a Python **stdlib**
  app adds **zero** new dependencies.

## Approach (decided)

**Delivery:** browser handles the login leg; the learner performs the token exchange **by hand**
with `curl`. Emphasis throughout is on *understanding each leg*, not just running commands.

**A real app at `localhost:3000`** (not a dead landing page). Chosen behavior — **"App catches
the code, learner does the exchange"**:

- The app serves a "Log in with Keycloak" page that builds the `/auth` authorization URL
  (including a `state` value).
- Its callback route catches the redirect, verifies `state`, and **displays exactly what the app
  received** — the `code` and `state`, and pointedly **not** the password.
- The callback page renders a **pre-filled `curl`** for the back-channel token exchange. The
  learner runs it themselves — the leg where `client_secret` proves the app's identity.

This preserves both requirements: a working page (no dead-page hack) **and** the token exchange
done by hand. The "the app only ever received a `code`, never the password" moment is the core
security lesson.

**Stack:** Python **stdlib `http.server`**, a single short, readable file run via a new
`make webapp` target (foreground process, Ctrl-C to stop). The file is intentionally readable —
it is teaching material, not a black box. Not a container; not in `docker-compose.yml`.

## Components

### 1. The callback app — `webapp/app.py` (new)

Single-file Python stdlib HTTP server on port 3000. Zero third-party imports.

Responsibilities:

- `GET /` — landing page with a **"Log in with Keycloak"** link. The link is the authorization
  URL, built server-side so the learner can read every parameter:
  `.../realms/corp/protocol/openid-connect/auth?response_type=code&client_id=corp-app&redirect_uri=http://localhost:3000/callback&scope=openid&state=<random>`.
  `state` is generated per request (stdlib `secrets`) and stashed so the callback can verify it.
- `GET /callback` — reads `code` and `state` from the query string, verifies `state` matches
  (CSRF guard — a teaching callout, not just a check), and renders a page that shows:
  1. **What the app received:** the `code` (single-use, ~60 s) and `state`. Explicit note: *no
     password reached this app.*
  2. **What to do next:** a copy-pasteable `curl` performing the exchange, with the real
     `code`, `client_id`, `client_secret`, `redirect_uri`, and token URL filled in.
- Constants at the top of the file (realm URL, client id/secret, redirect URI, port) so the
  learner can see — and, in the ROPC/confidential-client discussion, understand — where the
  secret lives.

Keep the HTML minimal and inline; no templates, no static assets. Comments explain each leg.

Note on the redirect URI: the app uses `/callback`; `redirectUris` is `http://localhost:3000/*`,
which already permits it — no realm change.

### 2. Makefile — `make webapp` target (new)

```
make webapp   ## Start the local callback app on :3000 (Ctrl-C to stop)
```

Runs `python3 webapp/app.py` in the foreground. Add a one-line pointer to it in the `up`/`demo`
help output is out of scope; a `.PHONY` entry and a `##` help comment are sufficient. The target
prints a one-line reminder of the URL to open (`http://localhost:3000`).

### 3. `lab.md` — new step + coherence edits

**New step, inserted after the current Step 2 (by-hand ROPC mint):**

> ### Step 3 — Run the flow a real app uses (Authorization Code)

Reframes the earlier ROPC steps as **"the shortcut"** and introduces the code flow as **"what a
real application does."** Walks the four legs, each with a *what just happened / why it matters*
callout:

1. **The redirect out.** `make webapp`, open `http://localhost:3000`, click "Log in." The app
   redirects the **browser** to Keycloak. Callout: the app never handles credentials; `state` is
   the CSRF guard.
2. **Login at the IdP.** The **real Keycloak login page** appears. Log in as `analyst` /
   `analyst123` — **into Keycloak, not the app.** This is the point of the whole flow.
3. **The redirect back.** Browser lands on the app's `/callback`; the app shows the `code` and
   `state` it received. Callout: the `code` is single-use, short-lived, and **useless without the
   `client_secret`** — the direct answer to "why is the secret there?"
4. **The back-channel exchange.** Run the pre-filled `curl` the app rendered: `code` +
   `client_secret` + `redirect_uri` → tokens. Callout: this server-to-server channel is where the
   secret proves the app; the browser never sees it.

Close the loop: the resulting token is the **same shape** and validates with the **same**
`validate-token.py` — identity is about *how the token was obtained*, not the token itself. The
existing steps renumber accordingly.

**Coherence edits to keep the lab whole:**

- **Flight card:** amend the real-handles/grant material so ROPC-vs-Authorization-Code is one of
  the things to hold (adjust #6 or add a 7th row).
- **Warm-up:** add one retrieval question — *which grant lets the app see the user's password,
  and why is that the anti-pattern?*
- **Recall check:** add one question walking "user clicks login → app allows request" through the
  redirect legs (extends the existing Q1 rather than duplicating it).
- **Deliverable `oidc-analysis.md`:** add a short section — the four legs, and **where the
  password went** in each of the two grants.
- **Definition of done:** add one checkbox — ran the browser Authorization Code flow and did the
  exchange by hand.
- **Marketable proof:** tweak to name **both** grants and why the redirect flow is the secure
  default.

### 4. PKCE — stretch item (new bullet in Stretch)

Add a stretch that layers PKCE (`code_challenge` / `code_verifier`) framed as *what protects a
**public** client — an SPA or mobile app that cannot keep a secret*. Deepens the "why does the
secret exist" thread without bloating the core path. Config note only for `corp-app` (confidential
clients may use PKCE but do not require it); the illustrative case is a public client.

## Data flow (the new step)

```
Browser                       App (:3000)                 Keycloak (:8080)
   | click "Log in"               |                              |
   |----------------------------->| build /auth URL + state      |
   | 302 to Keycloak /auth  <-----|                              |
   |------------------------------------ GET /auth ------------->|
   |                              |          login page  <-------|
   | submit analyst/analyst123 (PASSWORD GOES HERE, TO KEYCLOAK) |
   |------------------------------------ POST login ----------->|
   | 302 to :3000/callback?code=&state=  <----------------------|
   |----------------------------->| /callback: verify state,     |
   |                              | show code (NO password),     |
   |  page with pre-filled curl <-| render exchange curl         |
   |                                                             |
   | learner runs curl by hand:  code + client_secret --------->| token endpoint
   |                                          tokens  <----------|  (back channel)
```

## Error handling / edge cases

- **`state` mismatch** on `/callback` → the app shows a clear "state did not match — possible CSRF"
  message instead of proceeding. Teaching moment, not a stack trace.
- **Missing `code`** (e.g. user hit `/callback` directly, or Keycloak returned `error=`) → the app
  surfaces the error/`error_description` query params rather than crashing.
- **Port 3000 already in use** → `make webapp` fails fast with the OS error; documented as "stop
  the other process or it's a stale run."
- **Expired code at exchange time** (>~60 s) → Keycloak returns `invalid_grant`; the lab notes this
  is expected and is itself the "single-use, short-lived" lesson — just click Log in again.
- **Keycloak not up** → the login redirect fails; the lab points back to `make up`.

## Testing / verification

Manual, matching the lab's "watch it happen" pedagogy — there is no grader:

1. `make up` → `make webapp`; open `http://localhost:3000`, click Log in.
2. Confirm the **Keycloak** login page renders (URL is `:8080`, not `:3000`) — password leg is at
   the IdP.
3. Log in; confirm `/callback` shows a `code` and **no password anywhere**.
4. Run the rendered `curl`; confirm it returns an `access_token` / `refresh_token`.
5. Confirm that token decodes to the same claim shape as the ROPC token and passes
   `validate-token.py`.
6. Negative: hit `/callback?code=x&state=wrong` → app reports the state mismatch, does not proceed.
7. Negative: wait >60 s before exchanging → `invalid_grant`, as documented.

## File-change summary

| File | Change |
|------|--------|
| `webapp/app.py` | **new** — stdlib callback app (readable, commented) |
| `Makefile` | **new target** `webapp` (+ `.PHONY`, `##` help) |
| `lab.md` | new Step 3 (renumber following steps) + flight-card / warm-up / recall / deliverable / DoD / marketable-proof / stretch edits |
| `docker-compose.yml` | **no change** |
| `data/corp-realm.json` | **no change** (realm already supports the flow) |

## Open questions

None blocking. Placement (ROPC-as-shortcut, code-flow-as-payoff) and the make helper being
replaced by the app are both decided.
