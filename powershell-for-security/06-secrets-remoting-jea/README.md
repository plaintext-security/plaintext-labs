# Lab 06 — Secrets, Remoting & Least Privilege

Environment for **Track 13 · Module 06**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/06-secrets-remoting-jea/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer + Pester + SecretManagement/SecretStore container
make shell   # drop into pwsh
make demo    # gate: PSScriptAnalyzer + Pester (live secret round-trip + JEA .psrc/.pssc shape)
make down    # stop when done
```

- `Vigil/` — the cumulative reference module. This module adds `Get-VigilConfig` + `Set-VigilSecret`
  (SecretManagement-backed config, no plaintext creds), `Invoke-VigilRemote` (constrained remoting),
  and the JEA capability files under `Vigil/jea/`.
- `Vigil/jea/Vigil.ReadOnly.psrc` — the JEA **role capability**: exposes only Vigil's read-only hunt
  verbs (no state-changing cmdlets, no providers, no external commands).
- `Vigil/jea/Vigil.ReadOnly.pssc` — the JEA **session configuration** (`RestrictedRemoteServer`,
  virtual account, maps a group to the read-only role).
- `data/vigil.config.json` — non-secret config (vault name, secret name, feed URL). The **secret**
  itself never lives here — it is stored in and fetched from the vault by name.
- `data/sample.json` — the small Windows-event export carried from Module 01.

## Honest platform note

`SecretManagement` + `SecretStore` are cross-platform and are demonstrated **live** in this Linux
container (the `make demo` gate stores and retrieves a secret for real). **JEA enforcement and
PowerShell Remoting over WinRM are Windows-only** — the container validates that the JEA `.psrc`/`.pssc`
files are well-formed and read-only, but it cannot *enforce* them. Running the constrained endpoint
end-to-end is an **optional Windows-VM step** in `lab.md`; it is *assessed-not-demonstrated* here.
