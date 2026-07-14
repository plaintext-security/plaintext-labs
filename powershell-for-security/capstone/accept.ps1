#!/usr/bin/env pwsh
# accept.ps1 - capstone acceptance checks. These verify the STRUCTURE the rubric expects.
# They pass from day one on the scaffold's structural checks (manifest, explicit exports,
# analyzer) and report which functions are still stubs, so you can see progress toward "ship it".
# The rubric (rubric.md) is the real bar - this script is a fast structural gate, not a grader.

$ErrorActionPreference = 'Stop'
$fail = 0

function Test-Check {
    param([string]$Name, [scriptblock]$Body)
    try {
        & $Body
        Write-Output "  [PASS] $Name"
    }
    catch {
        Write-Output "  [FAIL] $Name - $($_.Exception.Message)"
        $script:fail++
    }
}

Write-Output '=== Structure ==='
Test-Check 'manifest resolves (Test-ModuleManifest)' {
    $null = Test-ModuleManifest "$PSScriptRoot/Vigil/Vigil.psd1"
}
Test-Check 'FunctionsToExport is explicit (never *)' {
    $data = Import-PowerShellDataFile "$PSScriptRoot/Vigil/Vigil.psd1"
    if ($data.FunctionsToExport -contains '*') { throw "FunctionsToExport uses '*'" }
    if (-not $data.FunctionsToExport)          { throw 'FunctionsToExport is empty' }
}
Test-Check 'every exported function resolves' {
    Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
    $data = Import-PowerShellDataFile "$PSScriptRoot/Vigil/Vigil.psd1"
    foreach ($fn in $data.FunctionsToExport) {
        if (-not (Get-Command $fn -Module Vigil -ErrorAction SilentlyContinue)) {
            throw "exported function $fn does not resolve"
        }
    }
}

Write-Output ''
Write-Output '=== Lint ==='
Test-Check 'PSScriptAnalyzer clean over ./Vigil' {
    $findings = Invoke-ScriptAnalyzer -Path "$PSScriptRoot/Vigil" -Recurse `
        -Settings "$PSScriptRoot/PSScriptAnalyzerSettings.psd1"
    if ($findings) { throw "$($findings.Count) analyzer finding(s)" }
}

Write-Output ''
Write-Output '=== Progress (stubs still to implement) ==='
Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
$data = Import-PowerShellDataFile "$PSScriptRoot/Vigil/Vigil.psd1"
foreach ($fn in $data.FunctionsToExport) {
    $src = (Get-Command $fn -Module Vigil).Definition
    $state = if ($src -match 'NotImplementedException') { 'STUB   ' } else { 'done   ' }
    Write-Output "  [$state] $fn"
}

Write-Output ''
if ($fail -gt 0) {
    Write-Error "$fail structural check(s) failed."
}
Write-Output 'Structural acceptance checks passed. Implement the stubs, then grade against rubric.md.'
