function Get-VigilEvent {
    <#
    .SYNOPSIS
        Ingest Windows telemetry (EVTX / JSON export) and emit raw event records. [CAPSTONE STUB]
    .DESCRIPTION
        Bring in your Module 03 implementation: Get-WinEvent server-side filtering over real
        .evtx (or a JSON export in the container), emitting typed objects - never Write-Host'd
        strings. This stub throws until you implement it; the acceptance checks expect real output.
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path
    )

    Write-Verbose "Get-VigilEvent stub called with -Path '$Path'."
    throw [System.NotImplementedException]::new(
        'Get-VigilEvent: bring in your Module 03 ingest implementation.')
}
