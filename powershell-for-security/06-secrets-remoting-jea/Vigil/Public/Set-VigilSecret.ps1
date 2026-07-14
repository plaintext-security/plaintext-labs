function Set-VigilSecret {
    <#
    .SYNOPSIS
        Stores a Vigil secret (token or credential) in a SecretManagement vault, by name.
    .DESCRIPTION
        A thin, auditable wrapper over Set-Secret so the module has one place that writes secrets and
        one place to review. It deliberately takes a [SecureString] (or a PSCredential), NOT a plain
        [string], so a plaintext literal cannot flow through it. This is the counterpart to
        Get-VigilConfig's GetToken(): write here, read there, and the secret never sits in source.
    .PARAMETER Name
        The secret's name in the vault (referenced by SecretName in vigil.config.json).
    .PARAMETER Secret
        The secret value as a SecureString. Prompt for it, or read it from an environment variable /
        CI secret at deploy time - never hardcode it.
    .PARAMETER Vault
        The target SecretManagement vault.
    .EXAMPLE
        $s = Read-Host -AsSecureString 'Feed API token'
        Set-VigilSecret -Name 'vigil-feed-token' -Secret $s -Vault 'VigilStore'
    #>
    [CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Medium')]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Name,

        [Parameter(Mandatory)]
        [ValidateNotNull()]
        [securestring]$Secret,

        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Vault
    )

    if ($PSCmdlet.ShouldProcess("secret '$Name' in vault '$Vault'", 'Set-Secret')) {
        Set-Secret -Name $Name -SecureStringSecret $Secret -Vault $Vault
    }
}
