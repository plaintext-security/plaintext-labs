# The validation layer - the security control of the whole module.
# Everything here sits between "arguments parsed from JSON" and "arguments used by a cmdlet".
# Treat every model-supplied value as untrusted input: parse, allow-list, type - reject the rest.

# The data root the MCP surface is allowed to read from. Model-supplied paths are confined to this.
$script:VigilDataRoot = (Resolve-Path "$PSScriptRoot/../../data").Path

function Resolve-VigilSafePath {
    <#
    .SYNOPSIS
        Resolve a model-supplied relative path and confine it to the allowed data root.
    .DESCRIPTION
        Rejects path traversal ('..'), absolute escapes, and any resolved path that lands outside the
        allowed root. Returns the full, confined path only when it is provably inside the root.
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Candidate,

        [string]$Root = $script:VigilDataRoot
    )

    # Reject anything that even looks like an escape before touching the filesystem.
    if ($Candidate -match '\.\.' -or [System.IO.Path]::IsPathRooted($Candidate)) {
        throw "path rejected (traversal or absolute path): $Candidate"
    }

    $rootFull = [System.IO.Path]::GetFullPath($Root)
    $sep      = [System.IO.Path]::DirectorySeparatorChar
    $full     = [System.IO.Path]::GetFullPath((Join-Path $rootFull $Candidate))

    if (-not $full.StartsWith($rootFull + $sep)) {
        throw "path escapes allowed root: $Candidate"
    }
    if (-not (Test-Path -Path $full -PathType Leaf)) {
        throw "path does not resolve to a file inside the allowed root: $Candidate"
    }
    $full
}

function ConvertTo-VigilValidatedArgument {
    <#
    .SYNOPSIS
        Validate the raw arguments of an MCP tools/call and return a typed splat for the target cmdlet.
    .DESCRIPTION
        The single choke point for untrusted LLM output. For each tool, every argument is validated -
        allow-listed enum, typed parse, confined path - BEFORE it is handed to a Vigil cmdlet. Anything
        invalid throws; the caller turns that into a safe MCP error, never a coerced or partial run.
    #>
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('Get-VigilEvent', 'Read-VigilEnrichment')]
        [string]$Name,

        # The raw arguments dictionary as parsed from the JSON-RPC request. Untrusted.
        $Raw
    )

    # Normalise the untrusted arguments object into a plain lookup over its keys.
    $bag = @{}
    if ($null -ne $Raw) {
        if ($Raw -is [hashtable]) {
            foreach ($k in $Raw.Keys) { $bag[[string]$k] = $Raw[$k] }
        }
        else {
            foreach ($p in $Raw.PSObject.Properties) { $bag[[string]$p.Name] = $p.Value }
        }
    }
    $get = { param($key) if ($bag.ContainsKey($key)) { $bag[$key] } else { $null } }

    switch ($Name) {
        'Get-VigilEvent' {
            $source = & $get 'source'
            if ([string]::IsNullOrWhiteSpace($source)) { throw "Get-VigilEvent: 'source' is required" }
            # Allow-list the source to a fixed set of bundled files - never a free-form path.
            $allowedSources = @{ 'sample' = 'sample.json' }
            if (-not $allowedSources.ContainsKey([string]$source)) {
                throw "Get-VigilEvent: 'source' not in allow-list: $source"
            }
            $path = Resolve-VigilSafePath -Candidate $allowedSources[[string]$source]

            $splat = @{ Path = $path }

            $severity = & $get 'severity'
            if ($null -ne $severity) {
                # Enumerated field -> ValidateSet-style allow-list. Reject anything else.
                if ([string]$severity -notin @('All', 'Suspicious')) {
                    throw "Get-VigilEvent: 'severity' not in allow-list: $severity"
                }
                $splat['Severity'] = [string]$severity
            }
            return $splat
        }

        'Read-VigilEnrichment' {
            $indicator = & $get 'indicator'
            if ([string]::IsNullOrWhiteSpace($indicator)) {
                throw "Read-VigilEnrichment: 'indicator' is required"
            }
            # An indicator is DATA - constrain its shape so it cannot smuggle a path or a command.
            $indicator = [string]$indicator
            if ($indicator.Length -gt 253 -or $indicator -notmatch '^[A-Za-z0-9_.:-]+$') {
                throw "Read-VigilEnrichment: 'indicator' has an unexpected shape: $indicator"
            }
            $feedPath = Resolve-VigilSafePath -Candidate 'threatfeed.json'
            return @{ Indicator = $indicator; FeedPath = $feedPath }
        }

        default {
            throw "no validator for tool: $Name"
        }
    }
}
