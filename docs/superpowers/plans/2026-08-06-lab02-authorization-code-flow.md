# Lab 02 — Authorization Code Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the OAuth2 Authorization Code flow to Lab 02 via a small, readable local callback app, so learners see the flow a real app uses — the password goes only to Keycloak, and the app redeems a one-time `code` with its `client_secret`.

**Architecture:** A single-file Python **stdlib** HTTP server (`webapp/app.py`) on port 3000 plays the confidential client. It serves a "Log in" page (builds the `/auth` URL + `state`), catches the `/callback` redirect, verifies `state`, shows the `code` it received (no password), and renders a pre-filled `curl` the learner runs by hand to exchange the code on the back channel. A `make webapp` target runs it. `lab.md` gains a new Step 3 walking the four legs, plus coherence edits so the flight card, warm-up, recall check, deliverables, and DoD stay whole.

**Tech Stack:** Python 3 standard library only (`http.server`, `urllib.parse`, `secrets`); `unittest` for tests; GNU Make; Keycloak 24 (unchanged).

## Global Constraints

- **Zero third-party dependencies.** `webapp/app.py` and its tests import from the Python **standard library only** (the lab is a curl/Docker lab that already leans on `python3`).
- **No realm change.** `corp-app` already has `standardFlowEnabled: true` and `redirectUris: ['http://localhost:3000/*']`; `data/corp-realm.json` and `docker-compose.yml` are **not** modified.
- **Exact real strings** (must match verbatim): realm `corp`; client `corp-app`; secret `corp-app-secret`; users `analyst`/`analyst123` and `admin`/`admin456`; Keycloak at `http://localhost:8080`; redirect URI `http://localhost:3000/callback`; app port `3000`.
- **Confidential client** — the core path uses `client_secret`, **not** PKCE. PKCE is a stretch item only.
- Tests run from the lab dir (`ztna/02-identity-control-plane`) with `PYTHONPATH=webapp python3 -m unittest test_app -v`.
- Commit messages end with the repo's required trailers (see each Commit step).

---

### Task 1: Callback app — pure helpers (URL, curl, HTML)

The testable core of the app: four pure functions with no network or server state. TDD with `unittest`.

**Files:**
- Create: `ztna/02-identity-control-plane/webapp/app.py` (helpers only in this task)
- Test: `ztna/02-identity-control-plane/webapp/test_app.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces:
  - `build_auth_url(state: str) -> str` — the Leg-1 authorization URL.
  - `build_exchange_curl(code: str) -> str` — the Leg-4 back-channel `curl` string.
  - `render_landing(state: str) -> str` — HTML for `GET /`.
  - `render_callback(query: dict[str, list[str]], expected_state: str) -> str` — HTML for `GET /callback`; `query` is the output of `urllib.parse.parse_qs` (values are lists).
  - `_page(title: str, body: str) -> str` — shared HTML shell.
  - Module constants: `KEYCLOAK_URL`, `REALM`, `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`, `PORT`, `AUTH_URL`, `TOKEN_URL`.

- [ ] **Step 1: Write the failing tests**

Create `ztna/02-identity-control-plane/webapp/test_app.py`:

```python
import unittest
from urllib.parse import urlparse, parse_qs
import app


class BuildAuthUrl(unittest.TestCase):
    def test_includes_required_params(self):
        q = parse_qs(urlparse(app.build_auth_url("abc123")).query)
        self.assertEqual(q["response_type"], ["code"])
        self.assertEqual(q["client_id"], ["corp-app"])
        self.assertEqual(q["redirect_uri"], ["http://localhost:3000/callback"])
        self.assertEqual(q["scope"], ["openid"])
        self.assertEqual(q["state"], ["abc123"])

    def test_points_at_auth_endpoint(self):
        self.assertIn("/realms/corp/protocol/openid-connect/auth",
                      app.build_auth_url("x"))


class BuildExchangeCurl(unittest.TestCase):
    def test_contains_grant_code_secret_redirect(self):
        c = app.build_exchange_curl("THECODE")
        self.assertIn("grant_type=authorization_code", c)
        self.assertIn("code=THECODE", c)
        self.assertIn("client_secret=corp-app-secret", c)
        self.assertIn("redirect_uri=http://localhost:3000/callback", c)
        self.assertIn("/protocol/openid-connect/token", c)


class RenderCallback(unittest.TestCase):
    def test_valid_code_shows_code_and_exchange(self):
        html = app.render_callback({"code": ["XYZ"], "state": ["s1"]}, "s1")
        self.assertIn("XYZ", html)
        self.assertIn("grant_type=authorization_code", html)

    def test_state_mismatch_refuses_and_hides_exchange(self):
        html = app.render_callback({"code": ["XYZ"], "state": ["bad"]}, "s1")
        self.assertIn("CSRF", html)
        self.assertNotIn("grant_type=authorization_code", html)

    def test_missing_code_reports_it(self):
        html = app.render_callback({"state": ["s1"]}, "s1")
        self.assertIn("No code", html)

    def test_keycloak_error_is_surfaced(self):
        html = app.render_callback(
            {"error": ["access_denied"], "error_description": ["user said no"]}, "s1")
        self.assertIn("access_denied", html)
        self.assertNotIn("grant_type=authorization_code", html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `ztna/02-identity-control-plane`): `PYTHONPATH=webapp python3 -m unittest test_app -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'` (or `AttributeError` once the file exists but is empty).

- [ ] **Step 3: Write the helpers**

Create `ztna/02-identity-control-plane/webapp/app.py`:

```python
#!/usr/bin/env python3
"""Lab 02 — Authorization Code flow callback app.

A deliberately small, readable OIDC confidential client. It lets you watch where
the password goes in the Authorization Code flow:
  - it redirects your BROWSER to Keycloak to log in (it never sees your password),
  - it CATCHES the redirect back and shows the one-time `code` it received,
  - it hands you the exact `curl` to redeem that code on the back channel, where
    the client_secret proves the app.

Run:  python3 webapp/app.py   (or `make webapp`), then open http://localhost:3000
Stop: Ctrl-C
"""
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs

KEYCLOAK_URL  = "http://localhost:8080"
REALM         = "corp"
CLIENT_ID     = "corp-app"
CLIENT_SECRET = "corp-app-secret"   # confidential client: the app proves itself with this
REDIRECT_URI  = "http://localhost:3000/callback"
PORT          = 3000

AUTH_URL  = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"


def build_auth_url(state):
    """Leg 1: the URL the app redirects the browser to. No credentials here — just
    who the app is (client_id), where to return (redirect_uri), what it wants
    (scope), and a CSRF token (state)."""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def build_exchange_curl(code):
    """Leg 4: the back-channel exchange, where client_secret proves the app. The
    browser never makes this call."""
    return (
        f"curl -s -X POST {TOKEN_URL} \\\n"
        f"  -d grant_type=authorization_code \\\n"
        f"  -d client_id={CLIENT_ID} \\\n"
        f"  -d client_secret={CLIENT_SECRET} \\\n"
        f"  -d redirect_uri={REDIRECT_URI} \\\n"
        f"  -d code={code} | python3 -m json.tool"
    )


def _page(title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head>"
            f"<body style=\"font-family:system-ui;max-width:44rem;margin:3rem auto;line-height:1.5\">"
            f"<h1>{title}</h1>{body}</body></html>")


def render_landing(state):
    url = build_auth_url(state)
    return _page(
        "Lab 02 — Authorization Code flow",
        f"<p>This app never sees your password. Clicking below sends your "
        f"<b>browser</b> to Keycloak to log in; the app only gets a one-time "
        f"<code>code</code> back.</p>"
        f"<p><a href=\"{url}\" style=\"display:inline-block;padding:.6rem 1rem;"
        f"background:#0b5;color:#fff;text-decoration:none;border-radius:6px\">"
        f"Log in with Keycloak</a></p>"
        f"<p style=\"color:#666\">The app will redirect your browser to:<br>"
        f"<code>{url}</code></p>")


def render_callback(query, expected_state):
    """Leg 3: what the app renders after Keycloak redirects back. `query` is the
    dict from parse_qs (values are lists). Handle error / missing-code / state
    mismatch before showing the code."""
    def one(key):
        vals = query.get(key)
        return vals[0] if vals else None

    if one("error"):
        return _page("Keycloak returned an error",
                     f"<p><b>{one('error')}</b>: {one('error_description') or ''}</p>"
                     f"<p>Start again from <a href='/'>the login page</a>.</p>")
    if not one("code"):
        return _page("No code in the callback",
                     "<p>This URL carried no <code>code</code>. Start at "
                     "<a href='/'>the login page</a>.</p>")
    if one("state") != expected_state:
        return _page("State did not match — possible CSRF",
                     "<p>The <code>state</code> the app sent is not the one that "
                     "came back, so the app refuses to proceed. That is the CSRF "
                     "guard doing its job. Start again from "
                     "<a href='/'>the login page</a>.</p>")

    code = one("code")
    curl = build_exchange_curl(code)
    return _page(
        "The app received a code",
        f"<p>Keycloak sent your browser back here with a one-time authorization "
        f"<code>code</code>. Notice what the app got: <b>only a code</b> — your "
        f"password went to Keycloak, never here.</p>"
        f"<p><b>code</b> (single-use, expires ~60s): <code>{code}</code></p>"
        f"<p><b>state</b> (verified against what the app sent): "
        f"<code>{one('state')}</code></p>"
        f"<h3>Now redeem it yourself — Leg 4, the back channel</h3>"
        f"<p>Run this in your terminal. The <code>client_secret</code> is what "
        f"proves the app; the browser never makes this call.</p>"
        f"<pre style=\"background:#f4f4f4;padding:1rem;overflow-x:auto\">{curl}</pre>")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONPATH=webapp python3 -m unittest test_app -v`
Expected: PASS — 7 tests OK.

- [ ] **Step 5: Commit**

```bash
git add ztna/02-identity-control-plane/webapp/app.py ztna/02-identity-control-plane/webapp/test_app.py
git commit -m "ztna/02: add Authorization Code callback app helpers

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01B3NqpTpVysKmRBebcJPPHi"
```

---

### Task 2: Wire the HTTP server and smoke-test it

Add the request handler and entry point to `app.py`, then run it and confirm the two routes serve real HTML. The handler is thin glue over Task 1's pure functions; its test is a manual smoke check (a live server is awkward to unit-test and not worth the machinery here).

**Files:**
- Modify: `ztna/02-identity-control-plane/webapp/app.py` (append handler + `__main__`)

**Interfaces:**
- Consumes: `render_landing`, `render_callback` from Task 1; `Handler.state` holds the last `state` issued (single-user lab).
- Produces: a runnable server — `python3 webapp/app.py` serves `GET /` (landing, mints a new `state`) and `GET /callback` (renders the callback using `Handler.state`).

- [ ] **Step 1: Append the handler and entry point to `app.py`**

Add to the end of `ztna/02-identity-control-plane/webapp/app.py`:

```python
class Handler(BaseHTTPRequestHandler):
    state = None  # single-user lab: remember the last state we handed out

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            self._send_html(render_callback(parse_qs(parsed.query), Handler.state))
        elif parsed.path in ("/", ""):
            Handler.state = secrets.token_urlsafe(16)
            self._send_html(render_landing(Handler.state))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # keep the lab console quiet


if __name__ == "__main__":
    print(f"Callback app on http://localhost:{PORT}  (Ctrl-C to stop)")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
```

- [ ] **Step 2: Confirm the unit tests still pass**

Run: `PYTHONPATH=webapp python3 -m unittest test_app -v`
Expected: PASS — 7 tests OK (appending the handler must not break the helpers).

- [ ] **Step 3: Smoke-test the running server**

Start it in the background and probe both routes:

```bash
python3 ztna/02-identity-control-plane/webapp/app.py &
APP_PID=$!
sleep 1
curl -s http://localhost:3000/ | grep -q "Log in with Keycloak" && echo "LANDING OK"
curl -s "http://localhost:3000/callback?error=access_denied&error_description=nope" | grep -q "access_denied" && echo "CALLBACK OK"
kill $APP_PID
```

Expected: prints `LANDING OK` and `CALLBACK OK`.

- [ ] **Step 4: Commit**

```bash
git add ztna/02-identity-control-plane/webapp/app.py
git commit -m "ztna/02: serve the callback app over http.server on :3000

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01B3NqpTpVysKmRBebcJPPHi"
```

---

### Task 3: `make webapp` target

Give the lab a one-command way to start the app, matching the existing `up`/`demo` idiom.

**Files:**
- Modify: `ztna/02-identity-control-plane/Makefile:6` (`.PHONY` line) and add a `webapp` target.

**Interfaces:**
- Consumes: `webapp/app.py` from Tasks 1–2.
- Produces: `make webapp` runs the app in the foreground.

- [ ] **Step 1: Add `webapp` to `.PHONY`**

Change line 6 of `ztna/02-identity-control-plane/Makefile` from:

```make
.PHONY: up down reset demo
```

to:

```make
.PHONY: up down reset demo webapp
```

- [ ] **Step 2: Add the `webapp` target**

Append to `ztna/02-identity-control-plane/Makefile` (after the `demo` target):

```make
webapp: ## Run the Authorization Code callback app on :3000 (Ctrl-C to stop)
	@echo "Callback app starting — open http://localhost:3000 in your browser."
	python3 webapp/app.py
```

- [ ] **Step 3: Verify the target is wired**

Run (from `ztna/02-identity-control-plane`): `make -n webapp`
Expected: prints the `echo` and `python3 webapp/app.py` lines without executing them.

- [ ] **Step 4: Commit**

```bash
git add ztna/02-identity-control-plane/Makefile
git commit -m "ztna/02: add make webapp target for the callback app

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01B3NqpTpVysKmRBebcJPPHi"
```

---

### Task 4: `lab.md` — new Step 3 + coherence edits

Add the Authorization Code step and update the surrounding scaffolding so the lab reads as a whole. No tests; verification is a careful re-read plus the end-to-end manual run in Task 5.

**Files:**
- Modify: `ztna/02-identity-control-plane/lab.md`

**Interfaces:**
- Consumes: `make webapp` (Task 3), the app's `/callback` page, `validate-token.py` (already referenced by the lab).
- Produces: renumbered steps (old Step 3 → 4, old Step 4 → 5) and the new Step 3.

- [ ] **Step 1: Insert the new Step 3**

In `ztna/02-identity-control-plane/lab.md`, immediately **after** the Step 2 "On track if" block (the paragraph ending `…re-run with the admin credentials.`) and **before** `### Step 3 — Find the blast-radius controls in the realm`, insert:

````markdown
### Step 3 — Run the flow a real app uses (Authorization Code)

**Concept (30 sec):** Steps 1–2 used the **password grant** (`grant_type=password`) — the
*shortcut*: you handed the user's password straight to `curl` playing the client. Real apps must
**never** see the password. The **Authorization Code flow** is how they avoid it — the password
goes only to Keycloak, and the app gets back a one-time `code` it redeems, with its
`client_secret`, on a back channel. Watch where the password goes in each leg.

**Do it:** start the callback app and walk the four legs.

```bash
make webapp    # serves http://localhost:3000 (Ctrl-C to stop when done)
```

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

Decode the `access_token` and compare it to your Step 2 analyst token: **same claims, same
signature, and it passes the same `validate-token.py`.** The token is identical — what changed is
that the app never saw the password. *That* is what the redirect flow buys you.

> **▸ On track if:** the login page you typed into was served by Keycloak on `:8080`; the app's
> callback page showed a `code` but **no password**; and the exchange `curl` returned an
> `access_token` whose claims match your Step 2 analyst token. If the exchange returns
> `invalid_grant`, the code expired (>60 s) or was already spent — click **Log in** again for a
> fresh one.

````

- [ ] **Step 2: Renumber the two following steps**

In `ztna/02-identity-control-plane/lab.md`:

- Change `### Step 3 — Find the blast-radius controls in the realm` to
  `### Step 4 — Find the blast-radius controls in the realm`.
- Change `### Step 4 — Reason about the two abuses: stolen token vs stolen key` to
  `### Step 5 — Reason about the two abuses: stolen token vs stolen key`.

(Do **not** touch the "Step 3 of the demo" / "Step 4 calls this out" phrases in Step 1's On-track
note — those refer to `make demo`'s internal steps, not the lab's numbered steps.)

- [ ] **Step 3: Update the flight card**

In `ztna/02-identity-control-plane/lab.md`:

- Change the heading `## ✈ Flight card — the 6 things to hold` to
  `## ✈ Flight card — the 7 things to hold`.
- After the table row that begins `| 6 | **The real handles:**`, add this new row:

```markdown
| 7 | **Two grants, opposite trust:** the **password grant** hands the *app* the user's password; **Authorization Code** sends it only to Keycloak. | ROPC is the shortcut (and OAuth 2.1-deprecated); the redirect flow is what real apps use. The `client_secret` proves the *app*, not the user. |
```

- Change `*(If you can explain all six cold at the end` to
  `*(If you can explain all seven cold at the end`.

- [ ] **Step 4: Add a warm-up question**

In the "Warm-up" section, after question 2 (`…one is on the clock, one is on the destination.)`),
add:

```markdown
3. Two OAuth grants show up in this lab: one sends the user's password **through the application**,
   the other sends it **only to the IdP**. Name which is which — and say why the second is the
   default for a real app.
```

- [ ] **Step 5: Add a recall-check question**

In the "Recall check" section, after question 3 (`…and which incident proved the second?`), add:

```markdown
4. In the Authorization Code flow, your password reached exactly one party and the app received
   exactly one thing. Name both — and say what makes the `code` useless to a thief who does not
   have the `client_secret`.
```

- [ ] **Step 6: Update the deliverable and step references**

In the Deliverables section, in the `oidc-analysis.md` bullet:

- Append to the end of that bullet (after `…labelled assessed-from-config.`):

```markdown
  Add a short **Authorization Code walkthrough** — the four legs (redirect out, login at the IdP,
  redirect back with the `code`, back-channel exchange) and, for each grant, **where the user's
  password went**.
```

- In that same bullet, change `(step 4b)` to `(step 5b)` and `(step 4c)` to `(step 5c)` (the abuse
  step moved from 4 to 5).

- [ ] **Step 7: Update Definition of done and Marketable proof**

In "Definition of done", after the checkbox `- [ ] You have manually minted and decoded tokens for
**both** users via curl…`, add:

```markdown
- [ ] You ran the **Authorization Code flow** in the browser (`make webapp`), logged in on
  Keycloak's own page, and **redeemed the `code` by hand** — and can say where your password went
  in each grant.
```

In "Marketable proof", change `walk a JWT token flow end-to-end *including signature validation
against the JWKS endpoint*` to `walk a JWT token flow end-to-end — *both the password grant and the
Authorization Code redirect flow, and why the redirect flow is the secure default* — including
signature validation against the JWKS endpoint`.

- [ ] **Step 8: Add the PKCE stretch item**

In the "Stretch" section, add a new bullet:

```markdown
- **PKCE for public clients.** `corp-app` is a *confidential* client — it proves itself with
  `client_secret`. A **public** client (an SPA or mobile app) can't keep a secret. Add
  `code_challenge` / `code_verifier` (PKCE) to the Authorization Code request and explain what PKCE
  puts in the secret's place, and why that closes the code-interception gap for clients that can't
  hold a secret.
```

- [ ] **Step 9: Sanity-check the edits**

Run (from `ztna/02-identity-control-plane`):

```bash
grep -n "^### Step" lab.md
grep -n "7 things to hold" lab.md
grep -n "step 5b\|step 5c" lab.md
```

Expected: steps read `Step 1, Step 2, Step 3 — Run the flow a real app uses (Authorization Code),
Step 4 — Find the blast-radius…, Step 5 — Reason about the two abuses`; the flight-card heading
shows "7 things to hold"; and the deliverable now references `step 5b` / `step 5c` (no lingering
`step 4b` / `step 4c`).

- [ ] **Step 10: Commit**

```bash
git add ztna/02-identity-control-plane/lab.md
git commit -m "ztna/02: add Authorization Code flow step and align lab scaffolding

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01B3NqpTpVysKmRBebcJPPHi"
```

---

### Task 5: End-to-end manual verification

Prove the whole thing works against a live realm, exactly as a learner will run it. No commit — this is the "watch it happen" gate.

**Files:** none (verification only).

- [ ] **Step 1: Bring up Keycloak and the app**

Run (from `ztna/02-identity-control-plane`):

```bash
make up        # wait for "Keycloak is ready."
make webapp    # leave running; open a second terminal for curl
```

- [ ] **Step 2: Walk the browser flow**

1. Open `http://localhost:3000`, click **Log in with Keycloak**.
2. Confirm the login page URL is on **`:8080`** (Keycloak), not `:3000`.
3. Log in as `analyst` / `analyst123`.
4. Confirm the callback page shows a **`code`** and a **`state`**, and **no password**.

- [ ] **Step 3: Do the exchange by hand**

Copy the `curl` the callback page rendered and run it. Confirm the JSON response contains an
`access_token` and a `refresh_token`.

- [ ] **Step 4: Confirm the token is equivalent to the ROPC token**

Decode the `access_token` (`jwt decode <token>` or pipe the middle segment through `base64 -d`) and
confirm `realm_access.roles` contains `analyst`, `azp` is `corp-app`, and `aud` is `corp-app` — the
same shape as the Step 2 token. If `validate-token.py` accepts a token string, confirm it passes;
otherwise confirm it decodes identically to the Step 2 analyst token.

- [ ] **Step 5: Confirm the two negative paths**

```bash
curl -s "http://localhost:3000/callback?code=x&state=wrong" | grep -c "CSRF"
```

Expected: `1` (the app refuses on a `state` mismatch). Then wait >60 s and re-run the exchange
`curl` from Step 3 — confirm Keycloak returns `invalid_grant` (the single-use / short-lived lesson),
and that clicking **Log in** again yields a fresh, working `code`.

- [ ] **Step 6: Tear down**

```bash
# Ctrl-C the `make webapp` process, then:
make down
```

---

## Self-Review

**Spec coverage** (each spec component → task):
- Callback app `webapp/app.py` (landing, `/callback`, state check, code+curl display) → Tasks 1–2.
- `make webapp` target → Task 3.
- `lab.md` new Step 3 (four legs) + flight card / warm-up / recall / deliverable / DoD / marketable-proof edits → Task 4.
- PKCE stretch → Task 4 Step 8.
- No realm / compose change → honored (only `webapp/`, `Makefile`, `lab.md` touched).
- Error handling (state mismatch, missing code, Keycloak error, expired code) → app: Task 1 tests + Task 2; expired-code lesson surfaced in lab Step 3 On-track and verified in Task 5 Step 5.
- Manual verification matching the lab's pedagogy → Task 5.

**Placeholder scan:** No TBD/TODO; all code and doc insertions are literal. HTML/curl strings are complete.

**Type consistency:** `build_auth_url(state)`, `build_exchange_curl(code)`, `render_landing(state)`, `render_callback(query, expected_state)`, `_page(title, body)` used consistently across Tasks 1–2 and tests. `Handler.state` is the single source of the expected state passed to `render_callback`. `render_callback` receives `parse_qs` output (list-valued dict) in both the handler and the tests.

**Note for the implementer:** Task 5 Step 4 says "if `validate-token.py` accepts a token string" — that validator is a learner deliverable, not shipped in this repo, so its exact CLI is unknown here; the decode-and-compare fallback is always valid.
