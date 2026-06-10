# Lab 11 — Build a Portfolio Repo (the Right Way)

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/11-version-control
make demo   # check git + print portfolio setup guide and secret-hygiene instructions
```

No Docker required. Git must be installed (`git --version` to confirm).
You also need a free [GitHub account](https://github.com/) to push your portfolio repo.

## Scenario
Create the repository you'll commit your curriculum deliverables to — and prove you can keep a
secret out of it.

## Do
1. [ ] Initialise a repo, make a few commits on a branch, and push it to GitHub.
2. [ ] Add a `.gitignore` that excludes secrets and lab artifacts (keys, `*.pcap`, logs).
3. [ ] Create a file that looks like a secret, confirm `.gitignore` keeps it untracked, and
   prove a real secret would not be committed.
4. [ ] Open a pull request from a branch and merge it — the collaboration loop.

## Success criteria — you're done when
- [ ] Your repo is on GitHub with a clean history and a sensible `.gitignore`.
- [ ] You demonstrated that an ignored secret file stays out of `git status`.
- [ ] You opened and merged a pull request.
- [ ] You can explain why deleting a committed secret isn't enough.

## Deliverables
A portfolio repo with a README and `.gitignore` — the home for every later deliverable.

## AI acceleration
Have a model draft your `.gitignore` and commit messages — then verify the ignore rules
actually cover the artifacts your labs produce, and that nothing it suggested rewrites shared
history.

## Connects forward
This is where every track's capstone lands, and the hygiene Track 08 (secret detection) and
Track 10 (CI/CD) build on.

## Marketable proof
> "I work in the open with git — branches, pull requests, clean history — and I keep secrets
> out of repos, exactly how detection-as-code and IaC teams operate."

## Automate & own it
**Required.** Add a pre-commit hook (or `gitleaks`) that blocks a commit containing a key — AI may
draft the config, but you verify it actually blocks a test secret, then commit it.

## Stretch
- Add a pre-commit hook (or try `gitleaks`) that blocks a commit containing a key — a preview
  of Tracks 08 and 10.
