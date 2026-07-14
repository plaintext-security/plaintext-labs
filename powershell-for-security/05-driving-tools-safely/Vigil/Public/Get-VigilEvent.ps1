function Get-VigilEvent {
    <#
    .SYNOPSIS
        Reads a JSON export of Windows events and emits the suspicious ones as typed objects.
    .DESCRIPTION
        Carried forward from Module 01 (the migrated hunt.ps1). Objects out, parameter validation in,
        PSScriptAnalyzer-clean. Kept in the cumulative Vigil module so later cmdlets compose with it.
    .EXAMPLE
        Get-VigilEvent -Path ./data/sample.json | Where-Object Suspicious
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path,

        # Attacker-ish tokens that mark an event suspicious.
        [string[]]$Token = @('IEX', 'DownloadString', '-enc', 'FromBase64String', 'hidden')
    )

    $events = Get-Content -Path $Path -Raw | ConvertFrom-Json

    foreach ($e in $events) {
        $hit = $false
        foreach ($t in $Token) {
            if ($e.Message -match [regex]::Escape($t)) { $hit = $true; break }
        }
        [pscustomobject]@{
            TimeCreated = [datetime]$e.TimeCreated
            Id          = [int]$e.Id
            Provider    = [string]$e.ProviderName
            Suspicious  = $hit
            Message     = [string]$e.Message
        }
    }
}
