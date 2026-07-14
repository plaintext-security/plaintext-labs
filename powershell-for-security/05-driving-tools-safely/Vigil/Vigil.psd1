@{
    RootModule        = 'Vigil.psm1'
    ModuleVersion     = '0.5.0'
    GUID              = 'b3c1e6a2-7f4d-4e9a-9c1b-0a2d3e4f5a6b'
    Author            = 'Plaintext learner'
    Description       = 'Vigil - Windows telemetry triage and hunt (Track 13 spine tool). v0.5: adds Invoke-VigilTool, an injection-safe external-process wrapper, plus the AST review gate.'
    PowerShellVersion = '7.4'
    # Explicit exports are the module boundary - never use '*'.
    FunctionsToExport = @('Get-VigilEvent', 'Invoke-VigilTool', 'Test-VigilNoInvokeExpression')
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
    PrivateData = @{
        PSData = @{
            Tags       = @('security', 'dfir', 'threat-hunting', 'windows-events')
            ProjectUri = 'https://github.com/plaintext-security/plaintext-labs'
        }
    }
}
