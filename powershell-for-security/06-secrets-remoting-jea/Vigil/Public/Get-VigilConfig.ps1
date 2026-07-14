function Get-VigilConfig {
    <#
    .SYNOPSIS
        Loads Vigil's runtime config, pulling any credential/token from SecretManagement -
        never from a plaintext literal in source.
    .DESCRIPTION
        Non-secret settings (endpoint host, feed URL, vault name) live in a committed JSON file.
        The SECRET itself (an API token, a service credential) is fetched by name from a registered
        SecretManagement vault at call time via Get-Secret. This is the whole discipline of the
        module: config in source, secrets in the vault. The copilot's default - a hardcoded
        $token = 'sk-...' or ConvertTo-SecureString -AsPlainText 'p@ss' - never appears here.
    .PARAMETER Path
        Path to the non-secret config JSON (defaults to ./data/vigil.config.json under the module root).
    .PARAMETER Vault
        The SecretManagement vault to resolve the secret from. Defaults to the vault named in the config.
    .EXAMPLE
        $cfg = Get-VigilConfig -Path ./data/vigil.config.json
        Invoke-RestMethod -Uri $cfg.FeedUrl -Headers @{ Authorization = $cfg.GetToken() }
    .OUTPUTS
        pscustomobject with the non-secret fields plus a GetToken() script method that resolves the
        secret lazily (so the token is never materialized until it is actually needed).
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path,

        [string]$Vault
    )

    $raw = Get-Content -Path $Path -Raw | ConvertFrom-Json

    # Resolve the vault: explicit parameter wins, else the config's declared vault.
    $vaultName = if ($Vault) { $Vault } else { [string]$raw.Vault }
    if (-not $vaultName) {
        throw 'No vault specified. Pass -Vault or set "Vault" in the config JSON.'
    }
    if (-not $raw.SecretName) {
        throw 'Config is missing "SecretName" - the name of the secret to resolve from the vault.'
    }

    $secretName = [string]$raw.SecretName

    # Return the non-secret config plus a lazy resolver. The secret is fetched only when GetToken()
    # is called, and is returned as plaintext ONLY at the moment of use - the config object itself
    # holds no credential material.
    $cfg = [pscustomobject]@{
        Vault      = $vaultName
        SecretName = $secretName
        FeedUrl    = [string]$raw.FeedUrl
        RemoteHost = [string]$raw.RemoteHost
    }

    $resolver = {
        # -AsPlainText returns the secret as a [string]; without it you get a [SecureString].
        # Callers that can consume a SecureString should call Get-Secret directly instead.
        Get-Secret -Name $this.SecretName -Vault $this.Vault -AsPlainText
    }
    $cfg | Add-Member -MemberType ScriptMethod -Name GetToken -Value $resolver -PassThru
}
