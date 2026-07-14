function Get-VigilMcpToolDefinition {
    <#
    .SYNOPSIS
        Return the MCP tool definitions Vigil advertises in tools/list.
    .DESCRIPTION
        Each definition is a name + description + inputSchema (JSON Schema). The schema is a HINT to the
        model about the shape to send - it is NOT a security control. Enforcement lives in the handler's
        validation layer (ConvertTo-VigilValidatedArgument). Schemas here are deliberately tight: enumerated
        values, no free-form command/script field, additionalProperties false.
    .EXAMPLE
        Get-VigilMcpToolDefinition | ConvertTo-Json -Depth 6
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param()

    @(
        [pscustomobject]@{
            name        = 'Get-VigilEvent'
            description = 'Return Windows events from a bundled log as objects, flagging suspicious ones. READ-ONLY.'
            inputSchema = [pscustomobject]@{
                type       = 'object'
                properties = [pscustomobject]@{
                    source   = [pscustomobject]@{ type = 'string'; enum = @('sample'); description = 'Which bundled log to read.' }
                    severity = [pscustomobject]@{ type = 'string'; enum = @('All', 'Suspicious'); description = 'Optional filter.' }
                }
                required             = @('source')
                additionalProperties = $false
            }
        },
        [pscustomobject]@{
            name        = 'Read-VigilEnrichment'
            description = 'Look up an indicator against a bundled threat-feed snapshot and return the verdict. READ-ONLY.'
            inputSchema = [pscustomobject]@{
                type       = 'object'
                properties = [pscustomobject]@{
                    indicator = [pscustomobject]@{ type = 'string'; description = 'The indicator (IP or hostname) to look up.' }
                }
                required             = @('indicator')
                additionalProperties = $false
            }
        }
    )
}
