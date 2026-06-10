# Module 11 — Version Control & Working in the Open

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *if it isn't committed, it didn't happen — and this whole curriculum is "commit the artifact."*

## Why this matters
Every capstone and deliverable here is "commit it to git." Version control is how you build a
portfolio, collaborate, and prove your work — and it's where secrets get leaked when people
are careless (the reason this repo ships a `.gitignore`). Git fluency is table stakes for any
security role that touches detection-as-code, IaC, or tooling.

## Objective
Use git confidently — branch, commit, push, and collaborate via pull requests — and keep
secrets and artifacts out of history.

## The core idea
This whole curriculum is "commit the artifact," so git isn't optional plumbing — it's how you build a
portfolio, prove your work, and collaborate, and it's table stakes for any role touching
detection-as-code, IaC, or tooling. The mental model worth holding: git is a *history of snapshots*,
and branches are just cheap pointers into that history — which is why the fork → branch → pull-request
flow (how the open-source world, and this project, collaborate) is the same three moves every time.

The security-specific reason this module exists, beyond fluency: **git history is forever**, and that
cuts both ways. It's why a portfolio of commits is credible — and why a leaked secret is the canonical
disaster. A key or token committed even once and "deleted" in a later commit is *still in history*,
retrievable by anyone who has the repo; the only real fix is to **rotate the secret**, not delete the
file. That's the entire reason this repo ships a `.gitignore` and treats secret hygiene as a standing
rule.

The judgment: models explain a git error or draft a commit message well, but they'll also confidently
propose history-rewriting commands (`reset --hard`, force-push) that can destroy work irrecoverably.
Understand any state-changing git command before you run it — git's safety net has holes, and "the AI
told me to force-push" is a bad incident story.

## Learn (~3 hrs)

**Git, properly**
- [Pro Git (free book)](https://git-scm.com/book/en/v2) — chapters 1–3 are the durable foundation; read, don't skim.
- [GitHub Skills](https://skills.github.com/) — short, interactive courses (intro, branching, pull requests) you do *in* a repo.
- [freeCodeCamp — Git and GitHub for Beginners Crash Course (~1 hr)](https://www.youtube.com/watch?v=RGOj5yH7evk) — a fast video pass if the book feels heavy; watch through the branching and pull-request sections.

**Hygiene**
- [git docs — gitignore](https://git-scm.com/docs/gitignore) — and study this repo's own `.gitignore` for what a security project must exclude.

## Key concepts
- Repos, commits, branches, and history
- Remotes: clone, push, pull
- Collaboration via fork + pull request
- `.gitignore` and keeping secrets/artifacts out of history
- Why a leaked secret in history is leaked *forever* (rotate, don't just delete)

## AI acceleration
Models are great at explaining a git error or drafting a commit message — but they'll also
confidently suggest history-rewriting commands (`reset --hard`, force-push) that can destroy
work. Understand any state-changing git command before you run it.
