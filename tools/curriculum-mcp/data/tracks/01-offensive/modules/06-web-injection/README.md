# Module 06 — Web Attacks: Injection

*Type 3 · Blast-Radius Trace — exploit SQL and command injection against a shipped vulnerable app, trace how far untrusted data reaches into the control plane, and end in the structural fix (parameterised queries). (Secondary: Misconception Reveal — injection isn't about SQL or "bad characters," it's data crossing into a control plane.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Offensive Security** — *the injection class that still pops databases decades later.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

!!! abstract "In 60 seconds"
    Injection happens whenever untrusted input crosses into an interpreter's control plane — a
    database, a shell, a template engine — and gets *parsed as code* instead of treated as data.
    SQLi, OS command injection, and XSS are all the same bug in different interpreters. The real fix
    isn't sanitising "bad characters" (blocklists always leak) — it's **parameterised queries**,
    which send structure and values over separate channels.

## Why this matters
Injection — SQL and OS command — happens whenever untrusted input is treated as code. It's
behind some of the largest breaches in history and remains everywhere because it's a design
mistake, not a single bug. Learning to find and exploit it (and later to fix it) is core
web-security literacy.

## Objective
Find and exploit SQL injection and command injection against a deliberately vulnerable app,
and explain the root cause and the fix.

## The core idea

**The bug is a parser with no boundary.** A database receives your query as one string of text,
and it cannot tell which parts of that string you *meant* as data and which you *meant* as
commands. When an app builds a query by pasting user input straight into the SQL —
`"... WHERE name LIKE '%" + input + "%'"` — a value like `' UNION SELECT username, password FROM
users-- ` stops being a search term and becomes new query *structure*. That's the entire bug: a
parser was handed a blend of trusted template and untrusted input with no boundary between the two,
so the attacker gets to finish writing the developer's query.

**SQL injection isn't really about SQL.** It's the same shape as OS command injection, LDAP
injection, XSS, server-side template injection, even log injection — untrusted data crossing into
some interpreter's control plane. You can find injection in any technology, including ones that
don't exist yet.

!!! note "The mental model"
    Once your mental question becomes "where does my input get *parsed* as code?", injection stops
    being a SQL trick and becomes a pattern you can spot in any interpreter.

!!! warning "The gotcha"
    The instinct to "sanitise the bad characters" is the wrong model: blocklists always leak
    (different quoting, encodings, second-order paths), and you end up playing whack-a-mole against
    a parser you don't control.

**The fix is structural, not defensive.** **Parameterised queries** (prepared statements) send the
query structure and the values over *separate channels*, so a value can never be reinterpreted as
structure no matter what bytes it contains. That's why it works where escaping fails — and as an
attacker it tells you exactly where to hunt: anywhere a developer was likely concatenating —
search, filters, `ORDER BY` columns, legacy endpoints, anything an ORM couldn't express cleanly.

??? note "Go deeper: an ORM is not immunity, and sqlmap is not understanding"
    An ORM is *not* immunity: raw fragments, dynamic column names, and `LIKE` clauses still bite.
    The catch in an engagement is that a finding only counts if you can reproduce and explain it;
    `sqlmap` automates the labour, never the understanding.

!!! tip "AI caveat"
    A model writes injection payloads fast — but it also produces ones that don't fit the context
    or that you can't explain, and a finding you can't reproduce is worthless in an engagement.
    Understand every payload you fire.

## Learn (~4 hrs)

**Hands-on labs (~3 hrs)**
- [PortSwigger Web Security Academy — SQL injection](https://portswigger.net/web-security/sql-injection) — the best free, hands-on labs anywhere; do the apprentice-level set.
- [PortSwigger — OS command injection](https://portswigger.net/web-security/os-command-injection) — the sibling class.

**Reference (~1 hr)**
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

!!! question "Check yourself"
    - In one sentence, what root cause do SQLi, OS command injection, and XSS all share?
    - Why do parameterised queries stop injection where escaping and character blocklists fail?
    - `sqlmap` confirms SQLi for you in an engagement — why isn't that finding ready to report yet?
