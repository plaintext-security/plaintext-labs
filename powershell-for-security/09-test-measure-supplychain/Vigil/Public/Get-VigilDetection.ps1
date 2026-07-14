function Get-VigilDetection {
    <#
    .SYNOPSIS
        Classifies a Windows event as malicious or benign - the detection the eval scores.
    .DESCRIPTION
        Vigil's detection for encoded / IEX-download-cradle PowerShell abuse (the Module 08
        technique, ATT&CK T1059.001 / T1027). Takes a VigilEvent-shaped object and returns a
        verdict object with a Predicted label ('malicious' or 'benign') and the tokens that
        matched. This is a binary CLASSIFIER - eval.ps1 scores it over a held-out labelled
        corpus and computes precision / recall / FP-rate.

        The detection is deliberately token-based and imperfect: the point of Module 09 is to
        MEASURE it on held-out data, not to assume it is correct. Removing a token (a planted
        regression) drops recall and the eval gate fails the build.
    .PARAMETER InputObject
        A VigilEvent-shaped object (must expose a .Message property). Accepts pipeline input.
    .PARAMETER Token
        The attacker-ish substrings that mark an event malicious. Matched case-insensitively
        as literals (not regex). Tuned against data/tuning/ ONLY - never the held-out set.
    .EXAMPLE
        Get-VigilEvent -Path ./data/heldout/malicious.json | Get-VigilDetection
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateNotNull()]
        [psobject]$InputObject,

        [ValidateNotNullOrEmpty()]
        [string[]]$Token = @(
            'IEX',
            'Invoke-Expression',
            'DownloadString',
            'DownloadFile',
            '-enc',
            '-EncodedCommand',
            'FromBase64String',
            '-w hidden',
            '-WindowStyle Hidden'
        )
    )

    process {
        $message = [string]$InputObject.Message
        $matched = [System.Collections.Generic.List[string]]::new()

        foreach ($t in $Token) {
            # Case-insensitive literal match - attacker casing varies (IEX / iex / Iex).
            if ($message -and $message.IndexOf($t, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                $matched.Add($t)
            }
        }

        [pscustomobject]@{
            Id        = $InputObject.Id
            Predicted = if ($matched.Count -gt 0) { 'malicious' } else { 'benign' }
            Matched   = $matched.ToArray()
            Message   = $message
        }
    }
}
