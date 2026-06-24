# Module 07 — Web & HTTP Fundamentals

*Variant D · skill-first, one light predict ("render the verdict" vein). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *almost every web attack and defense is just manipulating fields you can read in plain text.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules
{ .module-meta }

## The hook

In October 2010, a developer named Eric Butler released a Firefox extension called **Firesheep**. It
did one thing, and it did it with a single click: it watched the open wi-fi around you — a café, an
airport, a campus library — and listed every person nearby who was logged into Facebook, Twitter,
Flickr, and dozens of other sites. Double-click a name and you *were* them. No password, no cracking,
no exploit. ([Butler's release note](https://codebutler.com/2010/10/24/firesheep/) and the
contemporaneous [Wired write-up](https://www.wired.com/2010/10/firesheep/) cover the reaction.)

How? Those sites logged you in over HTTPS — the encrypted padlock page — and then dropped back to plain,
unencrypted **HTTP** for everything after. The thing your browser sent on every one of those later
requests, in the clear, was your **session cookie**: a short string the site handed you that means
"this is the person who logged in." Anyone sharing the wi-fi could read it off the air and replay it.
Firesheep just made that a button instead of a skill.

The fallout was the point: Firesheep embarrassed the industry into **HTTPS-everywhere** and into marking
session cookies `Secure` so the browser refuses to send them over plain HTTP. The fix is two settings
you can read in a response header — and this module is about reading them.

## Call it before you read on

You don't need to predict the whole protocol — you'll just *use* it in the lab. But hold one question,
because a beginner's gut answer here is wrong in a way the rest of web security depends on:

> **You're on café wi-fi, logged into a site over plain HTTP — the page works fine, you see your feed.
> The person at the next table runs Firesheep. What can they actually do, and what do they need from
> you to do it?**

Most people answer "they'd have to steal my password" or "guess it." Write down your guess. The real
answer is below, and it's smaller and scarier than that.

## The reveal — a session cookie is a temporary password

They need **nothing from you but proximity.** Here's the model to carry for the rest of the curriculum.

HTTP is **stateless**: the server forgets you the instant it answers a request. So "being logged in"
can't live on the server as a memory of you — it's *faked*. When you log in, the server generates a
random **session cookie** (e.g. `Set-Cookie: session=8f3a...`) and your **browser** stores it and
**re-sends it on every single request** automatically. The server sees that string come back and
thinks "ah, the person who logged in." That cookie is, functionally, **a temporary password the browser
keeps typing for you.**

Now the Firesheep twist: if the request travels over plain HTTP, that cookie crosses the wi-fi **in
cleartext** — readable by anyone on the same network. Copy the string, paste it into your own browser's
requests, and the server can't tell you apart from the real user. **No password needed, because the
cookie *is* the proof, and you have it.** That's session hijacking, and it's the whole reason web
security cares about three things you'll touch by hand in the lab:

- **HTTPS (TLS):** encrypts the request so the cookie can't be read off the wire in the first place.
- **The `Secure` cookie flag:** tells the browser *never* to send this cookie over plain HTTP — the
  exact setting whose absence Firesheep exploited.
- **The `HttpOnly` cookie flag:** hides the cookie from page JavaScript, so a script injected into the
  page can't read it either (a different theft path, same prize).

The judgment to keep: a security header or cookie flag being *present in best-practice advice* is not
the same as it being *present on the actual response*. You verify by reading the real exchange — which
is the skill, and why this module is built on `curl` rather than a browser.

## Learn (~3 hrs)

*Lean on purpose. Use these to go deeper on the mechanism — the model above is yours to own.*

**The protocol**
- [MDN — An overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview) (~30 min) — the canonical, readable reference for messages, methods, and status codes. Read it top to bottom; it's the spine.
- [MDN — Using HTTP cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies) (~25 min) — exactly how `Set-Cookie`, `Secure`, and `HttpOnly` work. Read the "Restrict access to cookies" section twice: that's the Firesheep fix.

**The security headers**
- [MDN — Strict-Transport-Security (HSTS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security) (~10 min) — the header that forces HTTPS so a downgrade to plain HTTP can't happen at all.
- [MDN — Content-Security-Policy (CSP)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy) (~15 min, orient only) — skim what it controls; it's the defense against injected scripts (the `HttpOnly`-adjacent threat).

**Reference (for the lab, not cover-to-cover)**
- [curl manual](https://curl.se/docs/manpage.html) — find `-v`, `-X`, `-d`, `-L`, `-c`, `-b`, `-H`. Half the lab is knowing which flag does what.
- [RFC 9110 — HTTP Semantics](https://datatracker.ietf.org/doc/html/rfc9110) and [RFC 6265 — HTTP State Management (cookies)](https://datatracker.ietf.org/doc/html/rfc6265) — the specs behind it. Reference, not reading.

## Key concepts
- Request anatomy (method · path · headers · body) and response anatomy (status · headers · body) — all plain text you can read and craft
- HTTP is **stateless**; cookies/sessions fake "logged in" by re-sending a token on every request
- A session cookie is a **temporary password** — whoever holds it is you, no password required (the Firesheep lesson)
- `Secure` (never send over plain HTTP) and `HttpOnly` (hide from page JavaScript) are the two flags that defend the cookie; HSTS forces HTTPS so the downgrade never happens
- A header's *presence in advice* ≠ its presence on the *actual response* — you verify by reading the raw exchange

## AI acceleration
Models explain an unfamiliar header or status code instantly, and will happily list "the security
headers a response should have." The judgment to keep: that's the *should*, not the *is*. Paste a model
the real response headers from your lab and ask which cookie flag is missing and what attack that
enables — then verify its answer against the raw `Set-Cookie` line yourself. The model drafts the
checklist; you confirm it against ground truth. You own the verdict.
