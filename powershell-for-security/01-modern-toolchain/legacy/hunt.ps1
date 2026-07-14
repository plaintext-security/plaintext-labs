# hunt.ps1 — the loose script you inherited. It WORKS. Do not "improve" it before you wrap it.
#
# Reads a JSON export of Windows events and prints a summary of the suspicious ones.
# Anti-patterns are intentional: Write-Host, positional params, a string-built filter,
# and no manifest / tests / analyzer pass. Your job in Lab 01 is to migrate it, not rewrite it.

param($Path = "$PSScriptRoot/../data/sample.json")

$events = Get-Content $Path -Raw | ConvertFrom-Json

# "suspicious" = a PowerShell script-block or process-creation event whose message
# contains one of these attacker-ish tokens.
$tokens = 'IEX', 'DownloadString', '-enc', 'FromBase64String', 'hidden'

$suspicious = @()
foreach ($e in $events) {
    foreach ($t in $tokens) {
        if ($e.Message -match [regex]::Escape($t)) {
            $suspicious += $e
            break
        }
    }
}

Write-Host "=== Vigil (hunt.ps1) — suspicious events ==="
Write-Host ("Total events: {0}" -f $events.Count)
Write-Host ("Suspicious:   {0}" -f $suspicious.Count)
Write-Host ""
foreach ($e in $suspicious) {
    Write-Host ("{0}  Id={1}  {2}" -f $e.TimeCreated, $e.Id, $e.Message)
}
