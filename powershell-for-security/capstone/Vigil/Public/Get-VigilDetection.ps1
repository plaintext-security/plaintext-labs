function Get-VigilDetection {
    <#
    .SYNOPSIS
        Classify an event as malicious or benign - the detection the eval scores. [CAPSTONE STUB]
    .DESCRIPTION
        Bring in your Module 08 detection (the encoded / AMSI PowerShell abuse you detonated and
        detected) and your Module 09 discipline: this is a binary classifier that eval.ps1 scores
        over a HELD-OUT labelled corpus. Return an object exposing a .Predicted label
        ('malicious' or 'benign'). This stub throws until you implement it.
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateNotNull()]
        [psobject]$InputObject
    )

    process {
        Write-Verbose "Get-VigilDetection stub received an object of type '$($InputObject.GetType().Name)'."
        throw [System.NotImplementedException]::new(
            'Get-VigilDetection: bring in your Module 08 detection + Module 09 eval discipline.')
    }
}
