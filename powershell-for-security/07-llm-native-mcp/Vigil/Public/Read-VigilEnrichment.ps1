function Read-VigilEnrichment {
    <#
    .SYNOPSIS
        Read-only: look up an indicator against a bundled threat-feed snapshot and return the verdict.
    .DESCRIPTION
        A read-only enrichment lookup exposed over the MCP surface. Takes a single indicator string and
        returns the matching feed record as a typed object, or a typed 'unknown' verdict when there is no
        match. Never mutates state; never runs the indicator - it is treated purely as data.
    .EXAMPLE
        Read-VigilEnrichment -Indicator '185.220.101.7' -FeedPath ./data/threatfeed.json
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Indicator,

        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$FeedPath
    )

    $feed = Get-Content -Path $FeedPath -Raw | ConvertFrom-Json
    $match = $feed | Where-Object { $_.Indicator -eq $Indicator } | Select-Object -First 1

    if ($match) {
        [pscustomobject]@{
            Indicator = [string]$match.Indicator
            Type      = [string]$match.Type
            Verdict   = [string]$match.Verdict
            Source    = [string]$match.Source
            FirstSeen = [string]$match.FirstSeen
        }
    }
    else {
        [pscustomobject]@{
            Indicator = [string]$Indicator
            Type      = 'unknown'
            Verdict   = 'unknown'
            Source    = 'no match in bundled feed'
            FirstSeen = $null
        }
    }
}
