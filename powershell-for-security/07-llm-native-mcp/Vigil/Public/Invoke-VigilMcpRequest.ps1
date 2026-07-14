function Invoke-VigilMcpRequest {
    <#
    .SYNOPSIS
        Handle one MCP JSON-RPC request (initialize / tools/list / tools/call) and return the JSON response.
    .DESCRIPTION
        A minimal, transport-agnostic MCP request handler - the offline stand-in for an MCP client talking
        over stdio. It does NOT require a network or a live model. The security-critical path is tools/call:
        the tool name is resolved from the read-only allow-list (Resolve-VigilTool), then every model-supplied
        argument is validated (ConvertTo-VigilValidatedArgument) BEFORE it reaches a cmdlet. A validation failure
        becomes a JSON-RPC error object the model can see - a safe rejection, never a coerced or partial run.
        No model-supplied value is ever passed into Invoke-Expression or any executable string.
    .EXAMPLE
        Invoke-VigilMcpRequest -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
    .EXAMPLE
        Invoke-VigilMcpRequest -Json '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"Get-VigilEvent","arguments":{"source":"sample","severity":"Suspicious"}}}'
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Json
    )

    $req = $null
    try {
        $req = $Json | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        return (@{
                jsonrpc = '2.0'
                id      = $null
                error   = @{ code = -32700; message = "parse error: $($_.Exception.Message)" }
            } | ConvertTo-Json -Depth 6 -Compress)
    }

    try {
        $result = switch ($req.method) {
            'initialize' {
                @{
                    protocolVersion = '2025-06-18'
                    capabilities    = @{ tools = @{} }
                    serverInfo      = @{ name = 'vigil'; version = '0.7.0' }
                }
            }
            'tools/list' {
                @{ tools = @(Get-VigilMcpToolDefinition) }
            }
            'tools/call' {
                $name = [string]$req.params.name
                # 1. Allow-list gate: only read-only, registered verbs resolve.
                $handler = Resolve-VigilTool -Name $name
                # 2. Validation layer: untrusted arguments become a typed, checked splat - or this throws.
                $validated = ConvertTo-VigilValidatedArgument -Name $name -Raw $req.params.arguments
                # 3. Only now is a cmdlet invoked, with values that have passed validation.
                $objects = & $handler $validated
                @{
                    content = @(
                        @{ type = 'text'; text = (@($objects) | ConvertTo-Json -Depth 6) }
                    )
                    isError = $false
                }
            }
            default {
                throw "unsupported method: $($req.method)"
            }
        }

        @{ jsonrpc = '2.0'; id = $req.id; result = $result } | ConvertTo-Json -Depth 8 -Compress
    }
    catch {
        # Any failure - unknown tool, failed validation, bad method - is a safe JSON-RPC error.
        @{
            jsonrpc = '2.0'
            id      = $req.id
            error   = @{ code = -32602; message = "invalid request or arguments: $($_.Exception.Message)" }
        } | ConvertTo-Json -Depth 6 -Compress
    }
}
