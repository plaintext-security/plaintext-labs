# Module 06 — Web Attacks: Injection

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *the injection class that still pops databases decades later.*

## Why this matters
Injection — SQL and OS command — happens whenever untrusted input is treated as code. It's
behind some of the largest breaches in history and remains everywhere because it's a design
mistake, not a single bug. Learning to find and exploit it (and later to fix it) is core
web-security literacy.

## Objective
Find and exploit SQL injection and command injection against a deliberately vulnerable app,
and explain the root cause and the fix.

## The core idea
A database receives your query as one string of text, and it cannot tell which parts of that
string you *meant* as data and which you *meant* as commands. When an app builds a query by
pasting user input straight into the SQL — `"... WHERE name LIKE '%" + input + "%'"` — a value
like `' UNION SELECT username, password FROM users-- ` stops being a search term and becomes new
query *structure*. That's the entire bug: a parser was handed a blend of trusted template and
untrusted input with no boundary between the two, so the attacker gets to finish writing the
developer's query.

Here's the part worth internalising: **SQL injection isn't really about SQL.** It's the same
shape as OS command injection, LDAP injection, XSS, server-side template injection, even log
injection — untrusted data crossing into some interpreter's control plane. Once your mental
question becomes "where does my input get *parsed* as code?", you can find injection in any
technology, including ones that don't exist yet. This is also why the instinct to "sanitise the
bad characters" is the wrong model: blocklists always leak (different quoting, encodings,
second-order paths), and you end up playing whack-a-mole against a parser you don't control.

The fix is structural, not defensive: **parameterised queries** (prepared statements) send the
query structure and the values over *separate channels*, so a value can never be reinterpreted as
structure no matter what bytes it contains. That's why it works where escaping fails — and as an
attacker it tells you exactly where to hunt: anywhere a developer was likely concatenating —
search, filters, `ORDER BY` columns, legacy endpoints, anything an ORM couldn't express cleanly.
(An ORM is *not* immunity: raw fragments, dynamic column names, and `LIKE` clauses still bite.)
The catch in an engagement is that a finding only counts if you can reproduce and explain it;
`sqlmap` automates the labour, never the understanding.

## Learn (~4 hrs)

**Hands-on labs**
- [PortSwigger Web Security Academy — SQL injection](https://portswigger.net/web-security/sql-injection) — the best free, hands-on labs anywhere; do the apprentice-level set.
- [PortSwigger — OS command injection](https://portswigger.net/web-security/os-command-injection) — the sibling class.

**Reference**
- [OWASP — SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection) — the canonical explanation and defenses.

## Key concepts
- Injection root cause: data crossing into a control plane (not "bad characters")
- UNION-based, error-based, and blind SQLi
- OS command injection as the same bug in a different interpreter
- Automating with `sqlmap` (and why you must understand it first)
- The fix: parameterised queries / safe APIs — separate channels for code and data

## AI acceleration
A model writes injection payloads and explains an error message fast — useful when you're
stuck. But it also produces payloads that don't fit the context or that you can't explain; in
an engagement, a finding you can't reproduce and explain is worthless. Understand every
payload you fire.
