# Lab 07 — Read the Cookie Firesheep Would Have Stolen

*Variant D · skill-first, one light predict. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs a tiny local
HTTP echo server (Flask) so you can read raw requests and responses with `curl` — no real site, no
attacking anyone.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/foundations/07-web-http
make up      # build + start the local echo server
make demo    # walk GET / POST / redirect / cookie / header in one pass
make shell   # drop into a shell with curl (server at http://echo-server:8080)
make down    # stop when done
```

## Scenario
You're profiling a small web app the way an analyst (or an attacker) would: by reading the exact bytes
it sends, not by trusting the browser. Somewhere in its responses is a session cookie set the way the
sites Firesheep hunted set theirs. Your job is to find it, name the flag that's missing, and say in one
sentence what the person on the next table could do with it.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against a server you started yourself.

## Do
Figure out the `curl` flags from its manual — knowing which flag does what is half the lab.

1. [ ] **See a request and response as plain text.** Make a GET to `/` and read the *full* request and
   response — method, path, status code, and every header (hint: `-v`). This is the raw material; an
   HTTP exchange is just text you can read.

2. [ ] **Carry state across two stateless requests.** Hit `/set-cookie` and capture what comes back,
   then send it on to `/cookie-echo` (hint: `-c` to save the jar, `-b` to send it). You've just proven
   that "being logged in" is nothing more than a string the client keeps handing back.

3. [ ] **Read the `Set-Cookie` line like an attacker.** Look closely at the `Set-Cookie` header from
   step 2. Which of `Secure` and `HttpOnly` are present, and which is missing? **Predict first:** with
   that flag missing and the site on plain HTTP, what does Firesheep get? Then confirm: the missing
   `Secure` flag is exactly what let the cookie travel in cleartext and be copied.

4. [ ] **Audit the security headers.** Check the response for `Strict-Transport-Security` (HSTS),
   `Content-Security-Policy`, and `X-Frame-Options` (hint: `-I` shows headers only). Note which are
   absent. Name the one header — HSTS — that, by forcing HTTPS, would have stopped the plain-HTTP
   downgrade Firesheep relied on.

5. [ ] **Tear down** the server when done (`make down`).

## Success criteria — you're done when
- [ ] You can identify the method, status code, and key headers in a raw exchange.
- [ ] You can explain how the cookie carried state between two otherwise stateless requests.
- [ ] You found the session cookie's **missing `Secure` flag** and can state, in one sentence, what an
  attacker on the same network does with a cookie sent in cleartext.
- [ ] You can name **HSTS** as the header that would have prevented the plain-HTTP downgrade, and say
  what `HttpOnly` defends against that `Secure` does not.

## Deliverables
`http-notes.md`: one annotated request/response pair (label each part), the exact `Set-Cookie` line with
the missing flag circled, and two sentences — *what* Firesheep stole and *which* flag/header would have
stopped it.

## Automate & own it
**Required.** Turn step 4 into a reusable **header-audit script** (`header_audit.py` or a `curl` wrapper):
given a URL, it fetches the response, then checks for `Strict-Transport-Security`, `Content-Security-Policy`,
and `X-Frame-Options`, and for any `Set-Cookie` it flags whether `Secure` and `HttpOnly` are present.
Output a clean PASS/MISSING line per check. **AI drafts the script; you review every line** — especially
that a missing flag is reported as missing and not silently passed — then commit it alongside `http-notes.md`.
Run it against your lab server (expect the missing `Secure`) and against a real HTTPS site to see the
contrast.

## AI acceleration
Paste your real response headers into a model and ask which cookie flag is missing and what attack it
enables. It will answer confidently — verify it against the actual `Set-Cookie` line, because the model
describes what *should* be there, not what *is*. Then ask it to draft your header-audit script and
review every check by hand.

## Connects forward
This raw-HTTP literacy is what Track 01's web modules (injection, broken access control, SSRF) and
Track 02's web telemetry assume. The "client controls the cookie, server trusts it" idea is the seed of
session-hijacking and broken-authentication bugs you'll exploit and detect later.

## Marketable proof
> "I can read and craft raw HTTP with curl — methods, headers, status codes, redirects, and cookies —
> and audit a response for the cookie flags and security headers that stop session hijacking. I can
> explain the Firesheep attack and the exact two settings that ended it."

## Stretch
- Run your header-audit script against `https://example.com` and a site you use daily: you'll see the
  TLS handshake (`curl -v`) but not the payload, and real `Secure; HttpOnly` cookies plus HSTS — the
  world Firesheep forced into existence. Tie the TLS half back to module 09.
