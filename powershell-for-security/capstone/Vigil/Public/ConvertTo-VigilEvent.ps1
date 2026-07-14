function ConvertTo-VigilEvent {
    <#
    .SYNOPSIS
        Normalize a raw event record into a typed VigilEvent object. [CAPSTONE STUB]
    .DESCRIPTION
        Bring in your Module 02 implementation: an advanced function with [OutputType] and
        parameter validation that turns a raw record into a typed VigilEvent - objects out,
        bad input rejected at the boundary. This stub throws until you implement it.
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateNotNull()]
        [psobject]$InputObject
    )

    process {
        Write-Verbose "ConvertTo-VigilEvent stub received an object of type '$($InputObject.GetType().Name)'."
        throw [System.NotImplementedException]::new(
            'ConvertTo-VigilEvent: bring in your Module 02 normalization implementation.')
    }
}
