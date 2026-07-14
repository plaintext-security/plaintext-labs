#!/usr/bin/env pwsh
# eval.ps1 - score Vigil's detection over the HELD-OUT labelled corpus and gate regressions.
#
# This is the Type-13 discipline made concrete: a held-out set + a metric + a regression gate.
#   * It scores ONLY data/heldout/ - never data/tuning/. Scoring on the tuning set would be a
#     memory test, not a generalization test.
#   * It reports precision / recall / FP-rate (accuracy is a trap on a benign-skewed corpus).
#   * It gates: recall must clear a FLOOR and FP-rate must stay under a CEILING. Below either,
#     the script Write-Errors and exits non-zero - a planted regression fails the build.
#
# No silent caps: this corpus is small (a handful of samples per class). The score proves the
# detection works ON THIS SET; it is a regression tripwire, not a claim of field accuracy.

[CmdletBinding()]
param(
    # The held-out split ONLY. Do not point this at data/tuning/.
    [string]$CorpusPath = "$PSScriptRoot/data/heldout",

    # Committed thresholds = the durable guarantee. Tune these against what the tool is for:
    # Vigil feeds a human hunter, so we lean toward recall (catch attacks) and accept some FPs.
    [double]$FloorRecall = 0.90,
    [double]$CeilFPRate  = 0.10
)

$ErrorActionPreference = 'Stop'
Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force

# --- Load the held-out corpus (each sample carries a ground-truth Label). ---
$labelled = foreach ($file in Get-ChildItem -Path $CorpusPath -Filter '*.json') {
    $events = Get-Content -Path $file.FullName -Raw | ConvertFrom-Json
    foreach ($e in $events) {
        [pscustomobject]@{
            Actual  = [string]$e.Label
            Message = [string]$e.Message
            Id      = [int]$e.Id
        }
    }
}

if (-not $labelled) {
    Write-Error "No labelled samples found under $CorpusPath."
}

# --- Run the detection over each sample and pair Predicted with Actual. ---
$scored = foreach ($sample in $labelled) {
    $verdict = $sample | Get-VigilDetection
    [pscustomobject]@{
        Id        = $sample.Id
        Actual    = $sample.Actual
        Predicted = $verdict.Predicted
    }
}

# --- Confusion counts. ---
$tp = ($scored | Where-Object { $_.Actual -eq 'malicious' -and $_.Predicted -eq 'malicious' }).Count
$fp = ($scored | Where-Object { $_.Actual -eq 'benign'    -and $_.Predicted -eq 'malicious' }).Count
$fn = ($scored | Where-Object { $_.Actual -eq 'malicious' -and $_.Predicted -eq 'benign'    }).Count
$tn = ($scored | Where-Object { $_.Actual -eq 'benign'    -and $_.Predicted -eq 'benign'    }).Count

# --- Metrics (guard against divide-by-zero). ---
$precision = if (($tp + $fp) -gt 0) { $tp / ($tp + $fp) } else { 0 }
$recall    = if (($tp + $fn) -gt 0) { $tp / ($tp + $fn) } else { 0 }
$fpRate    = if (($fp + $tn) -gt 0) { $fp / ($fp + $tn) } else { 0 }

# --- The scorecard (objects, then a readable table). ---
$scorecard = [pscustomobject]@{
    Samples   = $scored.Count
    TP        = $tp
    FP        = $fp
    FN        = $fn
    TN        = $tn
    Precision = [math]::Round($precision, 3)
    Recall    = [math]::Round($recall, 3)
    FPRate    = [math]::Round($fpRate, 3)
}

Write-Output '=== Vigil detection eval (held-out corpus) ==='
$scorecard | Format-List | Out-String | Write-Output

# --- The regression gate. ---
$failed = $false
if ($recall -lt $FloorRecall) {
    Write-Output ("REGRESSION: recall {0} < floor {1}" -f [math]::Round($recall, 3), $FloorRecall)
    $failed = $true
}
if ($fpRate -gt $CeilFPRate) {
    Write-Output ("REGRESSION: FP-rate {0} > ceiling {1}" -f [math]::Round($fpRate, 3), $CeilFPRate)
    $failed = $true
}

if ($failed) {
    Write-Error 'Detection eval FAILED the regression gate.'
}

Write-Output ("Eval PASSED: recall {0} >= {1}, FP-rate {2} <= {3}." -f `
    [math]::Round($recall, 3), $FloorRecall, [math]::Round($fpRate, 3), $CeilFPRate)
