#!/usr/bin/env pwsh
# The module gate: PSScriptAnalyzer over the Vigil module + Pester tests over the MCP surface.
# Exits non-zero if either fails - this is exactly what CI enforces.
# The Pester run feeds the tool-handler good AND hostile JSON-RPC payloads, entirely offline
# (no live LLM, no network), and proves hostile arguments are rejected by validation.

$ErrorActionPreference = 'Stop'

Write-Output '=== PSScriptAnalyzer: ./Vigil (the MCP-enabled module) ==='
$findings = Invoke-ScriptAnalyzer -Path "$PSScriptRoot/Vigil" -Recurse `
    -Settings "$PSScriptRoot/PSScriptAnalyzerSettings.psd1"
if ($findings) {
    $findings | Format-Table -AutoSize | Out-String | Write-Output
    Write-Error "PSScriptAnalyzer found $($findings.Count) issue(s) in the module."
}
Write-Output 'PSScriptAnalyzer: clean.'
Write-Output ''

Write-Output '=== Pester: Vigil.Tests.ps1 (good + hostile tool-argument payloads, offline) ==='
$config = New-PesterConfiguration
$config.Run.Path = "$PSScriptRoot/Vigil.Tests.ps1"
$config.Run.Exit = $true
$config.Output.Verbosity = 'Detailed'
Invoke-Pester -Configuration $config

Write-Output ''
Write-Output '=== Gate passed: analyzer-clean, tests green - hostile args rejected, surface read-only. ==='
