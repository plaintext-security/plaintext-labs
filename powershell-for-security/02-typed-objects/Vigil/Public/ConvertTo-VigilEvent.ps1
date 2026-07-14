function ConvertTo-VigilEvent {
    <#
    .SYNOPSIS
        Normalizes raw, untrusted event records into typed VigilEvent objects.
    .DESCRIPTION
        The Module 02 deliverable and the "objects, not strings" exemplar. Reads a JSON export of raw
        Windows event records - which may be messy (Id arriving as a string, a missing field) - and emits
        one typed [VigilEvent] object per VALID record. The input contract lives on the parameters
        (validation attributes), so bad input is rejected at the boundary; a record missing a required
        field is skipped with a warning rather than crashing the loop. Nothing is Write-Host'd: the console
        (or Sort-Object / Where-Object / Export-Csv) decides how the objects look.
    .PARAMETER Path
        Path to a JSON file of raw event records. Must exist and be a file (ValidateScript).
    .PARAMETER Token
        Attacker-ish tokens that mark an event Suspicious. Defaults to a small hunt list.
    .PARAMETER Level
        Optional filter: only emit events at one of these known severity levels (ValidateSet).
    .EXAMPLE
        ConvertTo-VigilEvent -Path ./data/raw-events.json | Where-Object Suspicious | Sort-Object TimeCreated
    .EXAMPLE
        ConvertTo-VigilEvent -Path ./data/raw-events.json -Level Warning | Export-Csv ./out.csv -NoTypeInformation
    #>
    [CmdletBinding()]
    [OutputType([VigilEvent])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path,

        [ValidateNotNullOrEmpty()]
        [string[]]$Token = @('IEX', 'DownloadString', '-enc', 'FromBase64String', 'hidden'),

        # Constrain to known severities - an unexpected level is a caller error, caught at the boundary.
        [ValidateSet('Information', 'Warning', 'Error', 'Verbose')]
        [string]$Level
    )

    $records = Get-Content -Path $Path -Raw | ConvertFrom-Json

    foreach ($record in $records) {
        # Untrusted input: a record missing a required field is skipped deliberately, not crashed on.
        if ([string]::IsNullOrWhiteSpace($record.TimeCreated) -or
            [string]::IsNullOrWhiteSpace($record.Id) -or
            [string]::IsNullOrWhiteSpace($record.Level) -or
            [string]::IsNullOrWhiteSpace($record.Message)) {
            Write-Warning "Skipping malformed record (missing a required field): $($record | ConvertTo-Json -Compress)"
            continue
        }

        if ($PSBoundParameters.ContainsKey('Level') -and $record.Level -ne $Level) {
            continue
        }

        $hit = $false
        foreach ($t in $Token) {
            if ($record.Message -match [regex]::Escape($t)) { $hit = $true; break }
        }

        # Emit a typed object. Fields are coerced to their REAL types (string Id -> [int]) by the constructor.
        [VigilEvent]::new(
            [datetime]$record.TimeCreated,
            [int]$record.Id,
            [string]$record.ProviderName,
            [string]$record.Level,
            $hit,
            [string]$record.Message
        )
    }
}
