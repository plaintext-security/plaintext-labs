@{
    RootModule        = 'Vigil.psm1'
    ModuleVersion     = '0.7.0'
    GUID              = 'b3c1e6a2-7f4d-4e9a-9c1b-0a2d3e4f5a6b'
    Author            = 'Plaintext learner'
    Description       = 'Vigil - Windows telemetry triage and hunt (Track 13 spine tool). v0.7: an MCP surface exposing read-only hunt verbs, with typed validation of untrusted LLM tool arguments.'
    PowerShellVersion = '7.4'
    # Explicit exports are the module boundary - never use '*'. Only read-only verbs plus the MCP entry point.
    FunctionsToExport = @(
        'Get-VigilEvent',
        'Read-VigilEnrichment',
        'Get-VigilMcpToolDefinition',
        'Invoke-VigilMcpRequest'
    )
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
    PrivateData = @{
        PSData = @{
            Tags       = @('security', 'dfir', 'threat-hunting', 'windows-events', 'mcp', 'llm')
            ProjectUri = 'https://github.com/plaintext-security/plaintext-labs'
        }
    }
}
