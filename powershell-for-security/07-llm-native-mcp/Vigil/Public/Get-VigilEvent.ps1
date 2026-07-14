function Get-VigilEvent {
    <#
    .SYNOPSIS
        Read-only: return Windows events from a JSON export as typed objects, flagging suspicious ones.
    .DESCRIPTION
        The spine hunt verb, carried forward from earlier modules. Reads a JSON export of Windows events
        and returns them as objects (never Write-Host'd strings), marking attacker-ish ones suspicious.
        This is one of the read-only verbs the MCP surface exposes; the MCP handler validates every
        model-supplied argument before it reaches this function.
    .EXAMPLE
        Get-VigilEvent -Path ./data/sample.json | Where-Object Suspicious
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path,

        # Optional severity filter. An enumerated allow-list - the same shape the MCP layer validates.
        [ValidateSet('All', 'Suspicious')]
        [string]$Severity = 'All',

        # Attacker-ish tokens that mark an event suspicious.
        [string[]]$Token = @('IEX', 'DownloadString', '-enc', 'FromBase64String', 'hidden')
    )

    $events = Get-Content -Path $Path -Raw | ConvertFrom-Json

    foreach ($e in $events) {
        $hit = $false
        foreach ($t in $Token) {
            if ($e.Message -match [regex]::Escape($t)) { $hit = $true; break }
        }

        if ($Severity -eq 'Suspicious' -and -not $hit) { continue }

        [pscustomobject]@{
            TimeCreated = [datetime]$e.TimeCreated
            Id          = [int]$e.Id
            Provider    = [string]$e.ProviderName
            Suspicious  = $hit
            Message     = [string]$e.Message
        }
    }
}
