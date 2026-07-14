#!/usr/bin/env pwsh
# The module gate: benign detonation -> PSScriptAnalyzer over Vigil + the detonator ->
# Pester (detection fires on the malicious sample, is quiet on the benign held-out sample).
# Exits non-zero if any stage fails - this is exactly what CI enforces.

$ErrorActionPreference = 'Stop'

Write-Output '=== Stage 1: benign detonation (encode -> decode -> run benign payload -> capture telemetry) ==='
& "$PSScriptRoot/data/Invoke-BenignDetonation.ps1"
Write-Output ''

Write-Output '=== Stage 2: PSScriptAnalyzer over ./Vigil and the detonator ==='
$findings = Invoke-ScriptAnalyzer -Path "$PSScriptRoot/Vigil" -Recurse `
    -Settings "$PSScriptRoot/PSScriptAnalyzerSettings.psd1"
$findings += Invoke-ScriptAnalyzer -Path "$PSScriptRoot/data/Invoke-BenignDetonation.ps1" `
    -Settings "$PSScriptRoot/PSScriptAnalyzerSettings.psd1"
if ($findings) {
    $findings | Format-Table -AutoSize | Out-String | Write-Output
    Write-Error "PSScriptAnalyzer found $($findings.Count) issue(s)."
}
Write-Output 'PSScriptAnalyzer: clean.'
Write-Output ''

Write-Output '=== Stage 3: Pester (detection fires on malicious, quiet on benign held-out) ==='
$config = New-PesterConfiguration
$config.Run.Path = "$PSScriptRoot/Vigil.Tests.ps1"
$config.Run.Exit = $true
$config.Output.Verbosity = 'Detailed'
Invoke-Pester -Configuration $config

Write-Output ''
Write-Output '=== Gate passed: detonation ran benign, module analyzer-clean, detection fires and is quiet on benign. ==='
