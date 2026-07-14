#!/usr/bin/env pwsh
# The module gate: PSScriptAnalyzer over the Vigil module + Pester tests.
# Exits non-zero if either fails - this is exactly what CI enforces.
#
# Module 06 gate scope, run LIVE on Linux:
#   - PSScriptAnalyzer over ./Vigil (all .ps1/.psm1/.psd1). The .psrc/.pssc JEA data files are not
#     PowerShell scripts and are validated in Pester (Import-PowerShellDataFile + Test-PSSessionConfigurationFile).
#   - Pester: a real SecretManagement/SecretStore secret round-trip, plus JEA capability-file shape.
#   - JEA *enforcement* and WinRM remoting are Windows-only and NOT exercised here (see lab.md).

$ErrorActionPreference = 'Stop'

Write-Output '=== PSScriptAnalyzer: ./Vigil (the module) ==='
$findings = Invoke-ScriptAnalyzer -Path "$PSScriptRoot/Vigil" -Recurse `
    -Settings "$PSScriptRoot/PSScriptAnalyzerSettings.psd1"
if ($findings) {
    $findings | Format-Table -AutoSize | Out-String | Write-Output
    Write-Error "PSScriptAnalyzer found $($findings.Count) issue(s) in the module."
}
Write-Output 'PSScriptAnalyzer: clean.'
Write-Output ''

Write-Output '=== Pester: Vigil.Tests.ps1 ==='
$config = New-PesterConfiguration
$config.Run.Path = "$PSScriptRoot/Vigil.Tests.ps1"
$config.Run.Exit = $true
$config.Output.Verbosity = 'Detailed'
Invoke-Pester -Configuration $config

Write-Output ''
Write-Output '=== Gate passed: module is analyzer-clean, secret round-trip works, JEA files are well-formed. ==='
