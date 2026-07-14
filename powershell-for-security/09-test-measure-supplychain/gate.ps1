#!/usr/bin/env pwsh
# The full Module 09 gate - four different questions, four checks:
#   1. STYLE        - PSScriptAnalyzer over the module.
#   2. CORRECTNESS  - Pester tests (mocks + unhappy paths) with a coverage FLOOR.
#   3. EFFECTIVENESS- eval.ps1 scores the detection on the HELD-OUT corpus + regression gate.
#   4. AUTHENTICITY - sign.ps1 signs the module and proves tampering is caught.
# Exits non-zero if ANY check fails - this is exactly what CI enforces.
# Coverage-green is not eval-green: a detection can have 100% coverage and still miss attacks.

$ErrorActionPreference = 'Stop'

Write-Output '=== [1/4] PSScriptAnalyzer: ./Vigil ==='
$findings = Invoke-ScriptAnalyzer -Path "$PSScriptRoot/Vigil" -Recurse `
    -Settings "$PSScriptRoot/PSScriptAnalyzerSettings.psd1"
if ($findings) {
    $findings | Format-Table -AutoSize | Out-String | Write-Output
    Write-Error "PSScriptAnalyzer found $($findings.Count) issue(s) in the module."
}
Write-Output 'PSScriptAnalyzer: clean.'
Write-Output ''

Write-Output '=== [2/4] Pester: tests + coverage floor ==='
$config = New-PesterConfiguration
$config.Run.Path                          = "$PSScriptRoot/Vigil.Tests.ps1"
$config.Run.Exit                          = $true
$config.Output.Verbosity                  = 'Detailed'
$config.CodeCoverage.Enabled              = $true
$config.CodeCoverage.Path                 = "$PSScriptRoot/Vigil"
# Coverage is a PRESENCE floor, not an effectiveness measure. Effectiveness is [3/4].
# HONEST CAP: the ForEach-Object -Parallel body in Invoke-VigilEnrichment runs in separate
# runspaces that Pester's coverage instrumentation does not capture, so the parallel lines
# read as "uncovered" even though the mocked tests exercise the function. The floor is set
# below the achievable ceiling for exactly this reason - a real limit, named, not hidden.
$config.CodeCoverage.CoveragePercentTarget = 50
Invoke-Pester -Configuration $config
Write-Output ''

Write-Output '=== [3/4] Detection eval: held-out scorecard + regression gate ==='
& "$PSScriptRoot/eval.ps1"
Write-Output ''

Write-Output '=== [4/4] Supply chain: sign the module + prove tamper-detection ==='
& "$PSScriptRoot/sign.ps1"
Write-Output ''

Write-Output '=== Gate passed: style + correctness + effectiveness + authenticity all green. ==='
