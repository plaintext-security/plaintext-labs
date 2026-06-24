# Module 11 — Version Control & Working in the Open

*Variant D · skill-first with a load-bearing predict-then-reveal. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *git never forgets. "Working in the open" means assuming everything you push is permanent and public — including the secret you deleted.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules (especially [10 · Scripting & Automation](../10-scripting/README.md))
{ .module-meta }

## Why this matters

Every deliverable in this curriculum ends the same way: *commit it to git.* Version control is how
you build a portfolio, collaborate, and prove your work — and it is the single most common place
people leak secrets without realizing it. Git fluency is table stakes for any security role that
touches detection-as-code, infrastructure-as-code, or tooling. So this module does two things at
once: it makes you fluent in the everyday git workflow, and it corrects the one misconception about
git that has cost real companies real breaches.

## Objective

Use git confidently — branch, commit, push, and collaborate via pull requests — and *prove* you
understand why a leaked secret in history is leaked forever, by planting one, finding it, and wiring
a hook that stops the next one.

## The everyday model (the part you just need to know)

Git is a **history of snapshots.** A *commit* is a labeled snapshot of your files at a moment in
time. A *branch* is just a cheap, movable pointer at one of those snapshots — making a branch costs
nothing, which is why the workflow is always the same three moves: branch off, commit your work,
then open a **pull request** (PR) to merge it back. A *remote* (usually GitHub) is a copy of that
history living on a server so others can see it and collaborate. That's the whole everyday loop:
clone → branch → commit → push → pull request → merge. The lab walks you through it for real, so the
README won't re-derive what the Learn links below explain step by step.

One property of that model is doing all the work in this module, and most beginners get it wrong.

## Predict it before you read on

Don't scroll. Commit to an answer — being wrong here is the entire point.

> **You're working on a project. You accidentally `git commit` a file containing a real password —
> say, an AWS access key. You notice a minute later, delete the line, and `git commit` again with
> the key removed. The bad version is no longer in your current files.**
>
> **Is the secret gone?**

Write down *yes* or *no* and one sentence of why.

## The reveal — git never forgets

**No. The secret is still there, in full, forever — until you actively rewrite history.**

Here is why, straight from the model above: a commit is a *snapshot*, and git's whole job is to keep
**every** snapshot so you can go back to any point. Your second commit didn't edit the first one; it
added a *new* snapshot on top. The first snapshot — with the key in it — is still in the chain.
Anyone with the repo can run `git log -p` (show every commit *with its diff*) or `git show <that
commit>` and read the key, plainly, as if you'd never "deleted" it. Deleting the file in a later
commit changes the *present*; it does nothing to the *past* the repo is built to preserve.

Two consequences follow, and they are the security core of this module:

- **To actually remove a secret from history you must *rewrite* history** — rebuild the chain of
  snapshots without the offending one. Tools exist for exactly this:
  [`git filter-repo`](https://github.com/newren/git-filter-repo) (the modern, recommended one) and
  the older [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/). They are surgery, not
  an undo button, and they rewrite commit IDs for everyone.
- **If the repo was ever pushed somewhere public, assume the secret is already stolen.** This is not
  paranoia. Bots continuously scrape new GitHub commits for credentials; published research and
  vendor reports have found freshly committed AWS keys being used by attackers **within minutes**.
  So rewriting history is necessary but not sufficient — **the only real fix is to rotate the
  secret** (revoke the old key, issue a new one). A deleted-and-rewritten key that an attacker
  already copied is still a live key.

This is not hypothetical. In 2022, **Toyota disclosed that an access key for a server holding
customer (T-Connect) email data had been sitting in a public GitHub repository for roughly five
years** before anyone noticed. The fix wasn't "delete the file" — it was rotate the key and assume
exposure for the whole window. That five-year window is the misconception above, scaled to a global
manufacturer: a credential, committed once, lives in history until someone makes it stop.

**The mental model to keep for the rest of your career:** *git is append-only and effectively
permanent; "working in the open" means treating everything you push as public and forever.* That's
also why this repo ships a `.gitignore` — the cheapest fix is the secret that never gets committed in
the first place.

## Learn (~2.5 hrs)

*Deliberately lean. The everyday loop and the reveal above are yours to own; read these to go deeper
on the mechanism, not to relearn the model.*

**The everyday workflow**
- [Pro Git, ch. 2–3 (free book)](https://git-scm.com/book/en/v2) (~1.5 hrs) — the durable
  foundation. Read ch. 2 (recording changes, viewing history) and ch. 3 (branching). Section 2.2
  (`git log`) is the tool you'll use in the lab to *find* the planted secret.
- [GitHub — About pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) (~15 min) — the collaboration loop, from the source. This is how open-source (and this project) actually merges work.

**Keeping secrets out**
- [git docs — gitignore](https://git-scm.com/docs/gitignore) (~15 min) — the syntax; then read this
  repo's own `.gitignore` to see what a security project must exclude (`*.pcap`, `*.key`, logs).
- [gitleaks](https://github.com/gitleaks/gitleaks) (~20 min) — the secret-scanner you'll wire into a
  pre-commit hook in the lab. Read the README's "Pre-Commit" section.
- [Pro Git §8.3 — Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) (~15 min) — what a `pre-commit` hook is and where it lives, so the lab's fourth step isn't magic.

## Key concepts
- A commit is a snapshot; history is an append-only chain of them — git keeps every version
- The everyday loop: clone → branch → commit → push → pull request → merge
- Deleting a secret in a later commit does **not** remove it; it lives in history until rewritten
- Rewriting history (`git filter-repo` / BFG) removes the snapshot; **rotating** the secret is the real fix
- Anything pushed public should be assumed scraped within minutes — rotate, don't just delete
- `.gitignore` (never commit it) and a pre-commit secret scan (catch it before commit) are the cheap, layered defenses

## AI acceleration
Models are great at explaining a git error or drafting a `.gitignore` or commit message. But two
cautions, both load-bearing for this module: first, a model will confidently propose
history-rewriting commands (`reset --hard`, `filter-repo`, force-push) that can destroy work
irrecoverably — understand any state-changing git command *before* you run it ("the AI told me to
force-push" is a bad incident story). Second, if you ask a model "I committed a secret and deleted
it, am I safe?", a careless one may say yes. You now know the answer is *rotate it.* You own that
judgment; the model assists it.
