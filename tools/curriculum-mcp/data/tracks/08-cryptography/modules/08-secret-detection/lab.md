# Lab 08 — Secret Detection & Leakage

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/08-secret-detection
make up        # build the container with gitleaks + trufflehog + seed git repo
make demo      # scan the seed repo with both tools, show findings
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally. The seed repository uses fake credentials in AKIAIOSFODNN7EXAMPLE
> format — they are not real AWS keys and are not verified.

## Scenario

Meridian Financial's security team has been asked to audit the payroll application repository
before a cloud migration. The repository has been in use for three years. Your job: scan the
full commit history for secrets, triage each finding, document which are live credentials
(if any), and write a remediation plan.

## Do

1. [ ] `make demo` — watch both tools scan the seed repository. Note: the commit hashes where
   secrets are found, the types of secrets detected (AWS key, API token, private key header),
   and whether any finding is "Verified: true".

2. [ ] `make shell` and scan the seed repo yourself with gitleaks, emitting a JSON report. For
   each finding, pull out which commit, which file, and which rule fired.

3. [ ] Find the commit whose message claims to *remove* the credential, then show that file at
   that commit and at the commit that introduced it. Is the secret still recoverable from
   history? What does that prove about "just deleting" a committed secret?

4. [ ] Scan the same repo with trufflehog and compare. Do the two tools surface the same set of
   secrets? Is there anything one finds that the other misses, and why might that be?

5. [ ] Write a remediation plan in `remediation-plan.md`:
   - List each secret found: type, commit, file, severity.
   - For each: rotation step (what to do immediately), history remediation step (git-filter-repo
     or BFG repo cleaner), and notification step (who to inform — any forks or mirrors?).
   - Recommend a pre-commit hook configuration to prevent recurrence.

6. [ ] Add a gitleaks pre-commit hook (via a `.pre-commit-config.yaml` referencing the gitleaks
   repo and pinned to a release). Document: what would it do when a developer tries to commit an
   API key, and what is the limitation of a pre-commit hook alone? (What if the developer runs
   `git commit --no-verify`?)

## Success criteria — you're done when

- [ ] You identified all planted secrets with gitleaks and confirmed they persist in history after deletion.
- [ ] You compared gitleaks and trufflehog output and noted the differences.
- [ ] You produced a remediation plan with rotation, history cleanup, and notification steps.
- [ ] You can explain why the pre-commit hook is necessary but not sufficient.

## Deliverables

`remediation-plan.md` — the finding inventory + remediation plan. Commit it.

## Automate & own it

**Required.** Write a shell script `secret-scan.sh` that: runs gitleaks against a repository
path (argument 1), outputs the finding count by rule type, and exits non-zero if any findings
are present. Wire it into a GitHub Actions workflow that runs on every pull request. Have an
AI draft the jq parsing for the report; you verify it counts findings correctly and produces
the correct exit code when zero findings are present.

## AI acceleration

Ask an AI to write a custom gitleaks rule for detecting a Meridian-format internal API key
(e.g. `MRDNSK-[A-Z0-9]{20}`). Test the rule: add a fake key in that format to a test file,
run gitleaks with the custom config, and confirm detection. Then remove the key and confirm
gitleaks finds it in history. The model drafts the TOML rule; you validate it catches what it
should and doesn't produce excessive false positives.

## Connects forward

The secret scanning pipeline you built here is the detection side of the secrets management
programme from module 07. Together they form a complete secrets posture: Vault for runtime
secrets (module 07), SOPS for git-safe configuration (module 07), and gitleaks/trufflehog for
catching what escaped (this module). Module 10 (Auditing Applied-Crypto Failures) includes a
secrets-in-code audit check.

## Marketable proof

> "I scanned a legacy git repository with gitleaks and trufflehog, identified secrets that
> persisted in history after deletion, and produced a prioritised remediation plan with
> rotation, history cleanup, and CI prevention controls."

## Stretch

- Use `git-filter-repo` to remove the committed secret from the repository history. Confirm
  that gitleaks no longer finds it after the history rewrite. Then explain: who else needs to
  be notified, and why is credential rotation still required even after history cleanup?
- Research GitHub's secret scanning feature: what credential types does it detect automatically,
  how does it notify repository owners, and what is the "push protection" feature?
