# The read-only tool registry - an EXPLICIT allow-list. Read-only is a property of the surface:
# there is no destructive tool to call, so a prompt-injected model cannot reach one.
# Every value is a script block that splats already-validated arguments into a read-only Vigil cmdlet.

$script:VigilTools = [ordered]@{
    'Get-VigilEvent'       = { param($ValidatedArgs) Get-VigilEvent @ValidatedArgs }
    'Read-VigilEnrichment' = { param($ValidatedArgs) Read-VigilEnrichment @ValidatedArgs }
}

# Verbs that must NEVER appear on the surface. Used by the gate to prove the surface stays read-only.
$script:VigilForbiddenVerbPattern = '^(Set|Remove|New|Invoke|Start|Stop|Add|Clear|Write|Update|Restart|Rename)-'

function Resolve-VigilTool {
    <#
    .SYNOPSIS
        Look up a tool handler by name from the read-only allow-list; reject anything not registered.
    #>
    [CmdletBinding()]
    [OutputType([scriptblock])]
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )
    if (-not $script:VigilTools.Contains($Name)) {
        throw "unknown or non-exposed tool: $Name"
    }
    $script:VigilTools[$Name]
}
