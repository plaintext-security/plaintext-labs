# CIS Windows 11 Level 1 — Hardening Script
# Run as Administrator in PowerShell.
# Each block applies one CIS control and includes the CIS ID reference.
# REVIEW EACH BLOCK before running — do not execute blindly.
# Tested on Windows 11 Enterprise 23H2.

#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

Write-Host "=== CIS Windows 11 Level 1 Hardening ===" -ForegroundColor Cyan
Write-Host "Applying controls. Each block reports its CIS ID." -ForegroundColor Yellow
Write-Host ""

# --- CIS 1.1.4 — Minimum password length (14 chars) ---
Write-Host "[CIS 1.1.4] Setting minimum password length to 14..." -ForegroundColor Green
$tmpFile = [System.IO.Path]::GetTempFileName()
secedit /export /cfg $tmpFile | Out-Null
(Get-Content $tmpFile) -replace "MinimumPasswordLength = \d+", "MinimumPasswordLength = 14" |
    Set-Content $tmpFile
secedit /configure /db secedit.sdb /cfg $tmpFile /areas SECURITYPOLICY | Out-Null
Remove-Item $tmpFile
Write-Host "  Done: minimum password length = 14" -ForegroundColor Gray

# --- CIS 1.1.1 — Enforce password history (24 passwords) ---
Write-Host "[CIS 1.1.1] Setting password history to 24..." -ForegroundColor Green
net accounts /uniquepw:24 | Out-Null
Write-Host "  Done: password history = 24" -ForegroundColor Gray

# --- CIS 1.2.2 — Account lockout threshold (5 attempts) ---
Write-Host "[CIS 1.2.2] Setting account lockout threshold to 5..." -ForegroundColor Green
net accounts /lockoutthreshold:5 | Out-Null
Write-Host "  Done: lockout threshold = 5" -ForegroundColor Gray

# --- CIS 1.2.1 — Account lockout duration (15 minutes) ---
Write-Host "[CIS 1.2.1] Setting account lockout duration to 15 minutes..." -ForegroundColor Green
net accounts /lockoutduration:15 | Out-Null
Write-Host "  Done: lockout duration = 15 min" -ForegroundColor Gray

# --- CIS 2.3.7.1 — Do not display last username at logon ---
Write-Host "[CIS 2.3.7.1] Hiding last username at logon screen..." -ForegroundColor Green
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "DontDisplayLastUserName" -Value 1 -Type DWord
Write-Host "  Done: DontDisplayLastUserName = 1" -ForegroundColor Gray

# --- CIS 2.3.7.4 — Machine inactivity limit (900 seconds) ---
Write-Host "[CIS 2.3.7.4] Setting machine inactivity limit to 900 seconds..." -ForegroundColor Green
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "InactivityTimeoutSecs" -Value 900 -Type DWord
Write-Host "  Done: InactivityTimeoutSecs = 900" -ForegroundColor Gray

# --- CIS 2.3.10.6 — Do not store LAN Manager hash ---
Write-Host "[CIS 2.3.10.6] Disabling LAN Manager hash storage..." -ForegroundColor Green
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "NoLMHash" -Value 1 -Type DWord
Write-Host "  Done: NoLMHash = 1" -ForegroundColor Gray

# --- CIS 2.3.11.5 — NTLMv2 only ---
Write-Host "[CIS 2.3.11.5] Setting LAN Manager authentication to NTLMv2 only..." -ForegroundColor Green
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LmCompatibilityLevel" -Value 5 -Type DWord
Write-Host "  Done: LmCompatibilityLevel = 5 (NTLMv2 response only, refuse LM & NTLM)" -ForegroundColor Gray

# --- CIS 18.4.3 — Disable SMBv1 ---
Write-Host "[CIS 18.4.3] Disabling SMBv1 server..." -ForegroundColor Green
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Write-Host "  Done: SMBv1 disabled" -ForegroundColor Gray

# --- CIS 18.9.12.1 — Disable AutoPlay ---
Write-Host "[CIS 18.9.12.1] Disabling AutoPlay for all drives..." -ForegroundColor Green
$autoPlayPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"
if (-not (Test-Path $autoPlayPath)) { New-Item -Path $autoPlayPath -Force | Out-Null }
Set-ItemProperty -Path $autoPlayPath -Name "NoDriveTypeAutoRun" -Value 255 -Type DWord
Write-Host "  Done: NoDriveTypeAutoRun = 255 (all drives)" -ForegroundColor Gray

# --- CIS 18.9.59.2 — Enable PowerShell Script Block Logging ---
Write-Host "[CIS 18.9.59.2] Enabling PowerShell Script Block Logging..." -ForegroundColor Green
$psLoggingPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
if (-not (Test-Path $psLoggingPath)) { New-Item -Path $psLoggingPath -Force | Out-Null }
Set-ItemProperty -Path $psLoggingPath -Name "EnableScriptBlockLogging" -Value 1 -Type DWord
Write-Host "  Done: Script Block Logging enabled" -ForegroundColor Gray

# --- CIS 9.x — Windows Firewall (all profiles on, inbound blocked) ---
Write-Host "[CIS 9.x] Ensuring Windows Firewall is enabled for all profiles..." -ForegroundColor Green
Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True
Set-NetFirewallProfile -Profile Domain,Private,Public -DefaultInboundAction Block
Write-Host "  Done: Firewall on, inbound blocked by default" -ForegroundColor Gray

Write-Host ""
Write-Host "=== Hardening complete. Reboot recommended for all settings to take effect. ===" -ForegroundColor Cyan
Write-Host "Run CIS-CAT Lite to score the result." -ForegroundColor Yellow
