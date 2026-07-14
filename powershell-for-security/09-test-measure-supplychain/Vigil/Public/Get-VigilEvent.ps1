function Get-VigilEvent {
    <#
    .SYNOPSIS
        Reads a JSON export of Windows events and emits them as typed objects.
    .DESCRIPTION
        The cumulative Vigil ingest function (from Module 01). Reads a JSON export of
        Windows events and returns each as a [pscustomobject] - objects out, never
        Write-Host'd strings, parameter validation in.
    .EXAMPLE
        Get-VigilEvent -Path ./data/heldout/malicious.json
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path
    )

    $events = Get-Content -Path $Path -Raw | ConvertFrom-Json

    foreach ($e in $events) {
        [pscustomobject]@{
            TimeCreated = [datetime]$e.TimeCreated
            Id          = [int]$e.Id
            Provider    = [string]$e.ProviderName
            Message     = [string]$e.Message
        }
    }
}
