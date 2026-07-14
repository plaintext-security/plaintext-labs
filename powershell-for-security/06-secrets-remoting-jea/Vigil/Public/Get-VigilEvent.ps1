function Get-VigilEvent {
    <#
    .SYNOPSIS
        Reads a JSON export of Windows events and emits typed objects (carried forward from Module 01).
    .DESCRIPTION
        The read-only hunt verb Vigil.ReadOnly exposes over the constrained endpoint. Objects out,
        parameter validation in, PSScriptAnalyzer-clean. Kept minimal here so the reference module
        stays focused on this module's additions (secrets, remoting, JEA).
    .EXAMPLE
        Get-VigilEvent -Path ./data/sample.json | Where-Object Suspicious
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path,

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
