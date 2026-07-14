function Get-VigilEvent {
    <#
    .SYNOPSIS
        Reads a JSON export of Windows events and emits typed objects (carried forward from Module 01).
    .DESCRIPTION
        The Module 01 spine function: reads a clean JSON export and returns each event as an object with a
        Suspicious flag, never a Write-Host'd string. Kept here so the Vigil module stays cumulative;
        Module 02 adds ConvertTo-VigilEvent for raw, untrusted records.
    .EXAMPLE
        Get-VigilEvent -Path ./data/raw-events.json | Where-Object Suspicious
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
