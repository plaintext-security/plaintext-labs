function Write-VigilLog {
    <#
    .SYNOPSIS
        Emits a single structured JSON log line (never Write-Host).
    .DESCRIPTION
        Structured logging is how a hunt tool stays machine-readable. Instead of Write-Host
        (which writes formatted text to the host and cannot be captured, filtered, or shipped),
        Write-VigilLog builds a [pscustomobject] with a timestamp, level, message, and any extra
        fields, then serializes it with ConvertTo-Json -Compress to ONE line on stdout. That line
        is valid JSON your SIEM, jq, or Get-VigilEvent-style parser can ingest verbatim.

        Level filtering is applied here: a message below the -MinimumLevel threshold is dropped,
        so verbose logs cost nothing in production.
    .PARAMETER Message
        The human-readable message. Always present in the emitted record.
    .PARAMETER Level
        Severity of this record. Default 'Info'.
    .PARAMETER Data
        Optional hashtable of extra structured fields merged into the record (e.g. @{ EventId = 4104 }).
    .PARAMETER MinimumLevel
        Records below this level are suppressed. Default 'Info'.
    .EXAMPLE
        Write-VigilLog -Message 'suspicious event' -Level Warning -Data @{ EventId = 4104; Host = 'WKS07' }
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Message,

        [ValidateSet('Debug', 'Info', 'Warning', 'Error')]
        [string]$Level = 'Info',

        [hashtable]$Data,

        [ValidateSet('Debug', 'Info', 'Warning', 'Error')]
        [string]$MinimumLevel = 'Info'
    )

    process {
        $rank = @{ Debug = 0; Info = 1; Warning = 2; Error = 3 }
        if ($rank[$Level] -lt $rank[$MinimumLevel]) { return }

        $record = [ordered]@{
            timestamp = (Get-Date).ToUniversalTime().ToString('o')
            level     = $Level
            message   = $Message
        }
        if ($Data) {
            foreach ($key in $Data.Keys) { $record[[string]$key] = $Data[$key] }
        }

        # One compact JSON object per line: structured, greppable, shippable. Not Write-Host.
        [pscustomobject]$record | ConvertTo-Json -Compress -Depth 5
    }
}
