#!/usr/bin/env pwsh
# The module gate: PSScriptAnalyzer over the Vigil module + Pester tests.
# Exits non-zero if either fails — this is exactly what CI enforces.
# The loose legacy/hunt.ps1 is deliberately excluded: it's the "before", not the gated module.

$ErrorActionPreference = 'Stop'

Write-Output '=== PSScriptAnalyzer: ./Vigil (the migrated module) ==='
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
Write-Output '=== Gate passed: module is analyzer-clean and tests are green. ==='
