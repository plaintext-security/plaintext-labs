@{
    RootModule        = 'Vigil.psm1'
    ModuleVersion     = '1.0.0'
    GUID              = 'f7a2c9d4-1b3e-4a5c-8d6f-2e0a9b7c4d1e'
    Author            = 'Plaintext learner'
    Description       = 'Vigil - Windows telemetry triage and hunt (Track 13 capstone). Ship it: typed, tested, gated, signed.'
    PowerShellVersion = '7.4'
    # Explicit exports are the module boundary - never use '*'. Add your public functions here
    # as you build them out across the phases.
    FunctionsToExport = @(
        'Get-VigilEvent',
        'ConvertTo-VigilEvent',
        'Invoke-VigilEnrichment',
        'Get-VigilDetection'
    )
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
