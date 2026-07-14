function Get-VigilEvent {
    <#
    .SYNOPSIS
        Reference migration of the loose hunt.ps1 into an advanced function that emits typed objects.
    .DESCRIPTION
        Reads a JSON export of Windows events and returns the suspicious ones as objects
        (never Write-Host'd strings). This is the end-state the Lab 01 migration converges toward -
        objects out, parameter validation in, PSScriptAnalyzer-clean.
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
