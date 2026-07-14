function Invoke-VigilEnrichment {
    <#
    .SYNOPSIS
        Enrich indicators against a threat feed CONCURRENTLY, throttled, no races. [CAPSTONE STUB]
    .DESCRIPTION
        Bring in your Module 04 implementation: ForEach-Object -Parallel with a bounded
        -ThrottleLimit, retry/backoff, $using: for outer-scope reads, and a thread-safe sink
        (ConcurrentBag, not @() with +=). This stub throws until you implement it.
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateNotNullOrEmpty()]
        [string[]]$Indicator,

        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$FeedPath,

        [ValidateRange(1, 32)]
        [int]$ThrottleLimit = 5
    )

    process {
        Write-Verbose ("Invoke-VigilEnrichment stub: {0} indicator(s), feed '{1}', throttle {2}." -f `
            $Indicator.Count, $FeedPath, $ThrottleLimit)
        throw [System.NotImplementedException]::new(
            'Invoke-VigilEnrichment: bring in your Module 04 concurrent-enrichment implementation.')
    }
}
