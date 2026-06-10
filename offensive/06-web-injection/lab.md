# Lab 06 — Exploit SQL Injection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships its own deliberately vulnerable app in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo (no external target
needed):

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/offensive/06-web-injection
make up        # start the vulnerable Meridian directory app → http://localhost:8080
make demo      # watch a benign search, then a UNION injection steal credentials
make down      # stop it when you're done
```

The app is a Flask "employee directory" with a `/search?name=` endpoint that concatenates your
input straight into a SQL query — and a `users` table the search should never be able to reach.
You'll reach it anyway. (`sqlmap` is the real tool you'll point at it; install it from your
package manager or run it from a container.)

## Scenario
Find and exploit SQL injection in the directory search, escalating from detection to full data
extraction — pulling the credentials out of the `users` table.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do
1. [ ] Hit `http://localhost:8080/search?name=Doe` and watch the JSON — note it echoes the SQL your
   input built. Now break it: what single character turns a search term into broken SQL? (The
   response shows you the error and the query.)
2. [ ] Work out how many columns the query returns and their types — you need this for a UNION.
   (Hint: the directory shows two fields per person.)
3. [ ] Craft a `UNION SELECT` that extracts `username, password` from the `users` table. Confirm you
   pulled `admin`'s credentials.
4. [ ] Re-run the same finding with **`sqlmap`** and have it dump the table contents. (Which flag dumps
   the data?) Compare: what did it automate that you did by hand?
5. [ ] State the root cause in one sentence, and rewrite the vulnerable line as a **parameterised
   query** — explain why that closes it where escaping wouldn't.

## Success criteria — you're done when
- [ ] You confirmed injection and extracted the `users` table via a crafted UNION.
- [ ] You can explain *why* the input was injectable (data crossing into the SQL control plane).
- [ ] You reproduced it with `sqlmap` and can say what it automated.
- [ ] You can write the parameterised-query fix and explain why it works structurally.

## Deliverables
`sqli.md`: the injectable parameter, the payloads that worked, the data extracted (redact the
secrets), the `sqlmap` command, and the parameterised-query fix.

## Automate & own it
**Required.** After exploiting by hand, script the extraction (a few lines of `requests`, or capture
the `sqlmap` invocation) and document exactly what it automated versus what you did manually. Have a
model draft the script; **you confirm every payload fires** against the app before trusting it. Commit
the writeup and the script.

## AI acceleration
Have a model explain a confusing SQL error or suggest the next payload — then confirm it works against
the running app and that you understand why. Don't submit a finding you can't reproduce by hand.

## Connects forward
Injection is one of three web classes here; module 07 (auth & access control) and 08
(SSRF/XXE/deserialization) cover the rest. The "untrusted data crossing into a control plane" mental
model from this lab is the same bug you'll meet again as command injection and SSTI.

## Marketable proof
> "I find, exploit, and explain SQL and command injection — from detection to data extraction
> to the correct parameterised-query fix."

## Stretch
- Switch the app's vulnerable line to a parameterised query, rebuild, and confirm your exploit now
  fails — you've gone attacker → fixer on the same bug.
- Try a **blind** variant: remove the query echo and re-find the injection using only boolean/timing
  differences.
