#!/usr/bin/env pwsh
# The module gate for Module 05: three layers, in order of how blunt they are.
#   1. AST scan   - hard ban on Invoke-Expression / iex anywhere in ./Vigil (parses the tree).
#   2. Analyzer   - PSScriptAnalyzer (PSAvoidUsingInvokeExpression and friends).
#   3. Pester     - proves a hostile argument fed to Invoke-VigilTool is DATA, not executed.
# Exits non-zero if any layer fails - this is exactly what CI enforces.

$ErrorActionPreference = 'Stop'

Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force

Write-Output '=== AST scan: no Invoke-Expression / iex in ./Vigil ==='
if (-not (Test-VigilNoInvokeExpression -Path "$PSScriptRoot/Vigil")) {
    Write-Error 'AST gate failed: a banned invocation (Invoke-Expression / iex) is present.'
}
Write-Output 'AST scan: clean.'
Write-Output ''

Write-Output '=== PSScriptAnalyzer: ./Vigil (the wrapper module) ==='
$findings = Invoke-ScriptAnalyzer -Path "$PSScriptRoot/Vigil" -Recurse `
    -Settings "$PSScriptRoot/PSScriptAnalyzerSettings.psd1"
if ($findings) {
    $findings | Format-Table -AutoSize | Out-String | Write-Output
    Write-Error "PSScriptAnalyzer found $($findings.Count) issue(s) in the module."
}
Write-Output 'PSScriptAnalyzer: clean.'
Write-Output ''

Write-Output '=== Pester: Vigil.Tests.ps1 (injection proofs + AST gate both ways) ==='
$config = New-PesterConfiguration
$config.Run.Path = "$PSScriptRoot/Vigil.Tests.ps1"
$config.Run.Exit = $true
$config.Output.Verbosity = 'Detailed'
Invoke-Pester -Configuration $config

Write-Output ''
Write-Output '=== Gate passed: no iex, analyzer-clean, and a malicious arg is proven inert. ==='
