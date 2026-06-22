# Lab 11 — Plant a Secret, Find It, Stop the Next One

*Variant D · skill-first + predict-then-reveal. [← Back to the module concept](README.md)*

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/11-version-control
make demo   # checks git is installed + prints the portfolio-repo guide and hygiene steps
```

No Docker required. You need git (`git --version` to confirm) and a free
[GitHub account](https://github.com/) to push your portfolio repo. The optional secret scanner
[gitleaks](https://github.com/gitleaks/gitleaks) is used in step 4 — `make scan` will tell you if
it's installed and how to get it.

> This lab plants a fake credential **in a repo you own** to teach you how history works. Never run
> secret-finding or history-rewriting commands against a repo you don't control.

## Scenario

You're creating the repository that every later deliverable in this curriculum lands in — your
portfolio repo. Along the way you'll *prove to yourself*, hands-on, that a deleted secret isn't gone:
you'll plant one, "delete" it, then find it still sitting in history. Finally you'll wire the cheap
defense that would have saved Toyota: a hook that refuses to commit a secret in the first place.

## Do

1. [ ] **The everyday loop — branch, commit, PR.**
   Initialise a repo (or create one on GitHub and clone it), make a couple of commits on a
   **branch** (not straight on `main`), push it, then open a **pull request** and merge it. Add a
   `README.md` describing the repo. *Hint:* `git switch -c <branch>`, `git add`, `git commit`,
   `git push -u origin <branch>`, then open the PR in GitHub's UI. This is the loop you'll repeat for
   the rest of the curriculum.

2. [ ] **Plant a secret, then "delete" it.**
   Create a file (e.g. `config.env`) containing a *fake* but real-looking credential — an AWS-style
   key is ideal (`AKIA...` plus a secret). Commit it. Then, in a **separate, later commit**, remove
   the line (or delete the file) so it's gone from your current working tree. Confirm with `git
   status` and a look at the file that the present is clean.
   **Predict — before the next step:** the secret is no longer in your files. Is it gone from the
   repo? Write down yes/no.

3. [ ] **Find it anyway — git never forgets.**
   Now prove the reveal yourself. Run `git log -p` (history *with diffs*) and find the commit where
   you added the key — there it is, in full. Confirm you can pull it back out of any single commit
   (*hint:* `git log` to get the commit ID, then `git show <id>`). Write one sentence in your repo's
   README answering your prediction: *why* deleting it didn't remove it, and what the *only* real fix
   is (rotate the secret; rewrite history with `git filter-repo` if it must leave the chain).

4. [ ] **Stop the next one — a pre-commit secret-scan hook.** *(This is "Automate & own it.")*
   Wire [gitleaks](https://github.com/gitleaks/gitleaks) as a `pre-commit` hook so git **refuses**
   any commit that contains a key. *Hint:* a hook is an executable script at
   `.git/hooks/pre-commit` that runs `gitleaks` (e.g. `gitleaks protect --staged`) and exits
   non-zero on a hit. **Prove it works:** stage a fresh fake key and try to commit — the commit must
   be blocked. Then add a real `.gitignore` (covering `*.key`, `*.pem`, `*.pcap`, logs, `config.env`)
   as the first, simplest layer.

## Success criteria — you're done when
- [ ] Your portfolio repo is on GitHub with a clean current tree, a `.gitignore`, and you opened and
  merged at least one pull request.
- [ ] You located the planted secret in history with `git log -p` / `git show` **after** "deleting"
  it, and can explain in one sentence why it was still there.
- [ ] You can state the real fix (rotate the secret; rewrite history if needed) — not "delete the file."
- [ ] Your pre-commit hook **blocks** a commit that contains a key (you demonstrated the block).

## Deliverables

Your portfolio repo: a `README.md`, a `.gitignore`, and a committed pre-commit hook config (or
setup notes for it) — the home for every later deliverable. Include the one-sentence explanation of
why a deleted secret survives in history. **Do not commit any real secret**, and once you've
demonstrated the planted fake, make sure it does not survive in the repo you submit (start a clean
repo for the deliverable if needed — that itself is the lesson).

## Automate & own it
**Required — and it's step 4.** The pre-commit gitleaks hook *is* the automation: it turns "remember
not to commit secrets" into a control that can't forget. Have a model draft the hook script and the
gitleaks config — then *you* verify it actually blocks a test key (and exits cleanly on a clean
commit), because a hook that silently passes everything is worse than none.

## AI acceleration
Ask a model to draft your `.gitignore`, your commit messages, and your pre-commit hook — then verify
every line: that the ignore rules cover the artifacts your labs produce, that the hook truly blocks a
planted key, and that nothing it suggested would rewrite *shared* history without you understanding
it. If you ask "I committed a secret and removed it — am I safe?", you already know to answer
*rotate it.*

## Connects forward
This repo is where every track's capstone lands. The hygiene reflex you built here is the seed of
**secret detection** and **CI/CD security** in later tracks — the same gitleaks scan, promoted from
your laptop to the whole team's pipeline.

## Marketable proof
> "I work in the open with git — branches, pull requests, clean history — and I keep secrets out of
> repos. I can show, hands-on, why a deleted secret survives in history, and I gate every commit with
> a secret scanner, exactly how detection-as-code and IaC teams operate."

## Stretch
- Take a throwaway repo where you committed a fake key, **rewrite it out of history** with
  [`git filter-repo`](https://github.com/newren/git-filter-repo), and confirm `git log -p` no longer
  shows it — then note why, in the real world, you'd *still* have rotated the key.
- Run `gitleaks detect` over the full history of an old repo of yours and see what it finds.
