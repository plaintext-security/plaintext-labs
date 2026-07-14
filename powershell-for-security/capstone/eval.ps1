#!/usr/bin/env pwsh
# Capstone eval stub - the detection eval + regression gate you build in Module 09, wired
# into the shipped module. Fill in the scoring; the SHAPE (held-out corpus -> scorecard ->
# regression gate, non-zero exit on a drop) is what the rubric grades.
#
# Rules that make this an eval and not a vibe:
#   * Score ONLY data/heldout/ - never a tuning set.
#   * Report precision / recall / FP-rate (NOT accuracy on a skewed corpus) and say why.
#   * Commit floors/ceilings; exit non-zero when a planted regression drops the score.
#   * No silent caps: note that a small corpus bounds what the score proves.

[CmdletBinding()]
param(
    [string]$CorpusPath  = "$PSScriptRoot/data/heldout",
    [double]$FloorRecall = 0.90,
    [double]$CeilFPRate  = 0.10
)

$ErrorActionPreference = 'Stop'
Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force

# 1. Load the held-out labelled corpus (each sample carries a ground-truth .Label).
# 2. Run Get-VigilDetection over each sample; pair Predicted with Actual.
# 3. Compute TP/FP/FN/TN -> precision / recall / FP-rate.
# 4. Print the scorecard, then FAIL (Write-Error / non-zero exit) below the floor / above the ceiling.

throw [System.NotImplementedException]::new(
    'eval.ps1: implement the held-out scorecard + regression gate (see Module 09).')
