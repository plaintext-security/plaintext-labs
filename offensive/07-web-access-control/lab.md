# Lab 07 — Break Access Control (IDOR + Privilege Escalation)

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/07-web-access-control
make up
```

The container runs a minimal Flask app (`app/app.py`) — Meridian Financial's
internal order portal — with two deliberate access-control bugs. No live
network required; the audit script uses Flask's test client.

## Scenario

Meridian's dev team shipped the internal portal quickly and tested it
"visually" — the UI hides the admin button from normal users, so it looks
right. But the server-side checks are broken in two ways. Find them, exploit
them, and state the fix.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Read `app/app.py` and find the two vulnerable functions before running anything.
   For each: which line is the bug, what trust assumption is wrong, and what does the
   server need to check instead? (`make demo` runs the validated exploit for both bugs —
   use it afterwards to confirm your reading and which HTTP status codes prove each one.)

2. [ ] Exploit the IDOR (Bug 1) yourself. `jsmith` is authenticated and owns orders 101
   and 103. Get the app to hand him an order he doesn't own and read another user's
   financial data. (What single value would you change, and what should the server have
   checked first?)

3. [ ] Exploit the vertical escalation (Bug 2). `jsmith` hitting `/api/admin/users` gets
   HTTP 403. Make the same request succeed as a non-admin. (The server trusts something
   the client controls — what header or field, and why is trusting it the bug?)

4. [ ] Build an access-control matrix for the orders: which users can read which order
   IDs, expected vs. actual. One non-owner can read another user's high-value order — find
   that cell yourself. What does it tell you about how to scope an audit?

5. [ ] Fix Bug 1: edit `app/app.py` and add the ownership check. Re-run
   `make demo` and confirm the IDOR returns HTTP 403 now.

6. [ ] Fix Bug 2: remove the `X-Role` header trust. Re-run and confirm the
   escalation returns HTTP 403 with the spoof header.

## Success criteria — you're done when

- [ ] You identified both vulnerable lines in `app/app.py` and can explain the root cause.
- [ ] You exploited IDOR to read another user's financial data (HTTP 200 on order 102).
- [ ] You bypassed the admin check via `X-Role: admin` (HTTP 200 on `/api/admin/users`).
- [ ] You applied both fixes and re-ran `make demo` to confirm both return 403.
- [ ] You can state the two-part principle: server-side enforcement + deny-by-default.

## Deliverables

`access-control.md`: for each bug — the vulnerable code snippet, the exploit
request, the HTTP response that proved it, and the fixed code. Include a
one-line risk statement per bug.

## Automate & own it

**Required.** Write `enumerate.py` that:
- Logs in as each user in a configurable list
- Tests every `GET /api/orders/<id>` from 100–110
- Outputs a table: which IDs each user can access vs. should be allowed to
- AI drafts the script; you review the authorization logic; commit it

## AI acceleration

Ask a model to generate a list of IDOR test IDs and role-escalation headers
to try for this app type. Then check each hypothesis in the running lab — the
model brainstorms, you confirm with real requests. Use a model to annotate
the `app.py` diff between vulnerable and fixed so you can explain each change.

## Connects forward

IDOR and privilege escalation are the top findings in web app pentests and
bug-bounty reports. Module 08 adds server-side request forgery (SSRF) and XXE
— a different attack surface on the same trust-the-server principle.

## Marketable proof

> "I find and exploit broken access control — IDOR and vertical privilege
> escalation — and explain the server-side ownership and deny-by-default fixes
> that close them."

## Stretch

- Build a full role × action matrix for the app: test every endpoint as
  every role (unauthenticated / user / admin). Record expected vs. actual
  status codes — this is how a real access-control audit is done.
- Add a JWT-based authentication variant to `app.py` where the role is encoded
  in the token claim. Demonstrate that tampering with an unsigned JWT bypasses
  the check the same way `X-Role` does.
