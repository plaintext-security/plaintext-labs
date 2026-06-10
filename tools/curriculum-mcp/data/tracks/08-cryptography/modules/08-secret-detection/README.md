# Module 08 — Secret Detection & Leakage

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *Secrets that escaped into source control don't expire when you remove them from the latest commit — they live in every clone of the repository's history.*

## Why this matters

Secret leakage in git repositories is one of the most consistently exploited entry points in cloud breaches. The pattern is predictable: a developer accidentally commits an AWS key or database password, catches it and deletes the file in the next commit — but the secret remains in the git history, accessible to anyone who clones the repository. Tools like gitleaks and trufflehog are designed specifically for this problem, scanning the full commit history rather than just the current state. Running them in CI is the control that catches secrets before they land in the remote; running them retrospectively is how you audit repositories that predate the control.

## Objective

Use gitleaks and trufflehog to scan a seed git repository with planted credentials across multiple commits — including one where the secret was "removed" in a subsequent commit — and demonstrate that the secret is still recoverable from history.

## The core idea

The core misconception that makes git secret leakage persistent is treating "I deleted the file" as equivalent to "I removed the secret." Git is an append-only log — it retains every version of every file in every commit. Removing a file in a new commit creates a new tree object without the file, but the old tree object (with the file) is still reachable from the previous commit's hash. Any clone of the repository, any CI/CD system that ran against an earlier commit, and any mirror or fork made before the deletion all retain the secret. The remediation for a committed secret is not a deletion commit — it is a credential rotation (assume the secret is compromised) followed by a history rewrite (`git filter-repo`) if access to the git host is needed for compliance, combined with the understanding that every clone made before the rewrite still has the old history.

gitleaks is a purpose-built git history scanner. It uses a rule set of regular expressions and entropy analysis to identify secrets in commits, file contents, and diff output. Its default ruleset covers AWS access keys (AKIA...), GitHub personal access tokens (ghp_...), private keys (BEGIN RSA/EC PRIVATE KEY), Stripe keys, Slack tokens, and hundreds of other patterns. gitleaks can scan a local repository, a remote URL, a specific commit range, or even a GitHub organisation's repositories in bulk. The key operational use is pre-commit hooks (catching secrets before they reach the remote) and CI checks (failing a pull request if a secret is detected).

trufflehog takes a different approach. Rather than relying primarily on regex patterns, trufflehog uses entropy analysis (identifying strings with high randomness — characteristic of keys and passwords) combined with verification: it attempts to call the relevant API with the detected credential to confirm it is a live, valid secret rather than a false positive. A trufflehog finding with "Verified: true" means the tool confirmed the credential works — this is a critical severity finding that warrants immediate rotation. A finding with "Verified: false" is a candidate false positive worth reviewing but not necessarily a live credential.

The pre-commit hook is the most important control in this module. A hook that runs gitleaks before every commit catches secrets at the developer workstation before they touch the remote. Configured organisation-wide via `.pre-commit-config.yaml` and enforced in CI (where commits that bypass local hooks can still be scanned), it creates a defence-in-depth posture: local hooks catch most secrets, CI is the backstop, and periodic retroactive scans of the full history find anything that slipped through before the controls were in place.

## Learn (~3 hrs)

**gitleaks**
- [gitleaks README (GitHub)](https://github.com/gitleaks/gitleaks) — read the installation, usage, and configuration sections; understand the rule format and how to add custom rules.
- [gitleaks rule set](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml) — browse the default ruleset; understand the regex patterns for AWS keys, GitHub tokens, and private key headers.

**trufflehog**
- [trufflehog README (GitHub)](https://github.com/trufflesecurity/trufflehog) — read the usage section, focusing on the `git` and `github` scanning modes and the verified/unverified distinction.

**Pre-commit hooks**
- [pre-commit framework documentation](https://pre-commit.com/) — the standard way to manage git hooks; understand how to add gitleaks as a pre-commit hook.

**Incident response context**
- [Git secret remediation guide (GitHub)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) — the official guide to removing secrets from git history with `git-filter-repo`; read to understand why rotation is the first step, not deletion.

## Key concepts

- Git history is permanent; "deleted" files are still reachable from previous commits in any clone.
- gitleaks: regex + entropy, full history scan, CI integration, pre-commit hooks.
- trufflehog: entropy + live verification; "Verified: true" = confirmed live credential = immediate rotation required.
- Remediation: rotate first (assume compromised), then rewrite history if required, then notify all forks/mirrors.
- Defence-in-depth: pre-commit hook (developer workstation) + CI check (remote) + periodic retrospective scan (history).

## AI acceleration

Ask an AI to generate a custom gitleaks rule for detecting Meridian Financial's internal API key format (e.g. `meridian-[a-z0-9]{32}`). Verify the regex matches your planted credential and does not match the benign strings in the repository. Then add the rule to `data/gitleaks.toml` and confirm gitleaks detects the custom pattern.
