function Invoke-VigilRemote {
    <#
    .SYNOPSIS
        Runs a Vigil read-only hunt verb on a remote WINDOWS host through the constrained
        Vigil.ReadOnly JEA endpoint - not a full admin Invoke-Command.
    .DESCRIPTION
        The least-privilege remoting path. Instead of opening an unconstrained admin session and
        running arbitrary script (the copilot's default), this connects to a specific JEA session
        configuration (-ConfigurationName 'Vigil.ReadOnly') that exposes ONLY Vigil's read-only hunt
        functions. Even a fully compromised caller can run nothing on the far end but those verbs.

        HONESTY / PLATFORM NOTE
        -----------------------
        PowerShell Remoting over WinRM and JEA *enforcement* are Windows-only. This function targets a
        Windows host; it cannot be exercised end-to-end from the Linux lab container (there is no WinRM
        listener and no JEA endpoint to constrain the session). It is authored and unit-tested for
        shape here, and is meant to be RUN against the optional Windows VM described in the module's
        lab.md, where Vigil.ReadOnly.pssc has been registered with Register-PSSessionConfiguration.
    .PARAMETER ComputerName
        The remote Windows host.
    .PARAMETER Command
        Which read-only hunt verb to invoke on the endpoint. Constrained to the exposed verbs so a
        caller cannot smuggle an arbitrary command string (no Invoke-Expression, no string-built line).
    .PARAMETER Credential
        The connecting identity. Resolve it from the vault (Get-Secret) - never a plaintext literal.
    .PARAMETER ConfigurationName
        The JEA session configuration to connect to. Defaults to the constrained 'Vigil.ReadOnly'.
    .EXAMPLE
        $cred = Get-Secret -Name 'vigil-remote-cred' -Vault 'VigilStore'
        Invoke-VigilRemote -ComputerName 'DC01' -Command Get-VigilEvent -Credential $cred
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', 'Command',
        Justification = 'Consumed via $using:Command inside the Invoke-Command scriptblock; the analyzer cannot see cross-scope use.')]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$ComputerName,

        # Whitelist of read-only verbs the endpoint is allowed to run. This mirrors the .psrc's
        # VisibleFunctions - the caller cannot ask for anything outside the constrained surface.
        [Parameter(Mandatory)]
        [ValidateSet('Get-VigilEvent')]
        [string]$Command,

        [Parameter(Mandatory)]
        [ValidateNotNull()]
        [pscredential]$Credential,

        [ValidateNotNullOrEmpty()]
        [string]$ConfigurationName = 'Vigil.ReadOnly'
    )

    # New-PSSession / Invoke-Command are Windows-only paths in practice (WinRM). Guard so the function
    # fails loudly with a clear message rather than a confusing WinRM error on a non-Windows host.
    if (-not $IsWindows) {
        throw ("Invoke-VigilRemote requires a Windows host with WinRM and the '$ConfigurationName' " +
               'JEA endpoint registered. See lab.md for the optional Windows-VM step; the Linux ' +
               'container cannot enforce JEA.')
    }

    $session = New-PSSession -ComputerName $ComputerName `
        -ConfigurationName $ConfigurationName `
        -Credential $Credential -ErrorAction Stop
    try {
        # Invoke the verb by name on the far end, passing it in with the $using: scope modifier.
        # The endpoint only exposes the constrained functions, so this resolves to a proxy function -
        # there is no string concatenation and no Invoke-Expression anywhere.
        Invoke-Command -Session $session -ScriptBlock {
            & $using:Command
        }
    }
    finally {
        Remove-PSSession -Session $session
    }
}
