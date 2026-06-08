# Windows Triage Collection Script
# Run on your Windows VM to collect the lab data.
# Usage: .\collect.ps1 > windows-recon.md

param([switch]$SkipEvents)

Write-Host "# Windows Recon — $(hostname) — $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-Host ""

# ── Local Administrators ─────────────────────────────────────────────────
Write-Host "## Local Administrators"
Write-Host ""
try {
    Get-LocalGroupMember -Group "Administrators" |
        Select-Object Name, PrincipalSource, ObjectClass |
        Format-Table -AutoSize | Out-String
} catch {
    net localgroup Administrators
}

# ── Auto-start Services ───────────────────────────────────────────────────
Write-Host "## Auto-start Services"
Write-Host ""
Get-Service | Where-Object {$_.StartType -eq 'Automatic'} |
    Select-Object Name, Status, DisplayName |
    Sort-Object Status -Descending |
    Format-Table -AutoSize | Out-String

# ── Registry Run Keys (persistence) ──────────────────────────────────────
Write-Host "## Registry Run Keys (persistence check)"
Write-Host ""
$runKeys = @(
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
)
foreach ($key in $runKeys) {
    if (Test-Path $key) {
        Write-Host "### $key"
        Get-ItemProperty $key | Format-List
    }
}

# ── Recent Logon Events ───────────────────────────────────────────────────
if (-not $SkipEvents) {
    Write-Host "## Recent Logon Events (EventID 4624, last 50)"
    Write-Host ""
    try {
        Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} -MaxEvents 50 -ErrorAction Stop |
            ForEach-Object {
                [PSCustomObject]@{
                    Time      = $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
                    User      = $_.Properties[5].Value
                    LogonType = $_.Properties[8].Value
                    IP        = $_.Properties[18].Value
                    Computer  = $_.MachineName
                }
            } | Format-Table -AutoSize | Out-String
    } catch {
        Write-Host "(Security log requires admin or audit policy enabled)"
    }
}

Write-Host "## EVTX Analysis"
Write-Host ""
Write-Host "Download EVTX attack samples from:"
Write-Host "  https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES"
Write-Host ""
Write-Host "Load a sample:"
Write-Host "  Get-WinEvent -Path .\sample.evtx | Select -First 20 | Format-List"
