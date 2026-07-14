function Get-VigilEvent {
    <#
    .SYNOPSIS
        Reads Windows event telemetry at scale and emits normalized, typed objects.
    .DESCRIPTION
        On a real Windows host you would point this at a live channel or an .evtx file via
        Get-WinEvent -FilterHashtable (server-side filtering by the Event Log API). Get-WinEvent
        is Windows-only, so in this cross-platform lab the events are pre-parsed from .evtx into
        JSONL by the 'evtx' Rust CLI (evtx_dump -o jsonl), and this function consumes that artifact.

        The discipline is identical either way: FILTER AT THE SOURCE, not with a trailing
        Where-Object. -EventId and -Provider are applied while records stream in, so the pipeline
        never materializes events you are going to discard. Output is one flat [pscustomobject] per
        event (TimeCreated, EventId, Provider, Computer, CommandLine, Suspicious, ...), never a
        Write-Host'd string.
    .PARAMETER Path
        Path to the JSONL export (one evtx_dump record per line).
    .PARAMETER EventId
        Keep only these Event IDs. Applied as records are read (source-side filter analogue).
    .PARAMETER Provider
        Keep only events from providers matching this wildcard (e.g. '*Sysmon*').
    .PARAMETER Token
        Attacker-ish substrings that mark an event Suspicious when found in its command/script text.
    .EXAMPLE
        Get-VigilEvent -Path ./data/events.jsonl -EventId 4104 -Provider '*PowerShell*'
    .EXAMPLE
        Get-VigilEvent -Path ./data/events.jsonl | Where-Object Suspicious
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path,

        [int[]]$EventId,

        [string]$Provider,

        [string[]]$Token = @(
            'IEX', 'DownloadString', '-enc', 'FromBase64String',
            'hidden', 'TCPClient', 'rundll32', '185.220.101.7'
        )
    )

    # Stream the export line by line so a large artifact never lands in memory whole.
    # Each line is a single evtx_dump record: { Event: { System: {...}, EventData: {...} } }.
    Get-Content -Path $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line) { return }

        $evt = ($line | ConvertFrom-Json).Event
        $sys = $evt.System
        $data = $evt.EventData

        $id = [int]$sys.EventID
        $prov = [string]$sys.Provider.'#attributes'.Name

        # Source-side filters: skip records we do not want BEFORE building an object for them.
        if ($EventId -and ($id -notin $EventId)) { return }
        if ($Provider -and ($prov -notlike $Provider)) { return }

        # Normalize the per-provider field into one 'command text' we can hunt over.
        $text = if ($data.CommandLine) { [string]$data.CommandLine }
        elseif ($data.ScriptBlockText) { [string]$data.ScriptBlockText }
        elseif ($data.DestinationIp) { "{0}:{1}" -f $data.DestinationIp, $data.DestinationPort }
        else { '' }

        $hit = $false
        foreach ($t in $Token) {
            if ($text -match [regex]::Escape($t)) { $hit = $true; break }
        }

        [pscustomobject]@{
            TimeCreated = [datetime]$sys.TimeCreated.'#attributes'.SystemTime
            EventId     = $id
            Provider    = $prov
            Computer    = [string]$sys.Computer
            User        = [string]($data.User | Select-Object -First 1)
            CommandLine = $text
            Suspicious  = $hit
        }
    }
}
