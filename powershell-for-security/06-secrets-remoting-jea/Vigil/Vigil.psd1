@{
    RootModule        = 'Vigil.psm1'
    ModuleVersion     = '0.6.0'
    GUID              = 'b3c1e6a2-7f4d-4e9a-9c1b-0a2d3e4f5a6b'
    Author            = 'Plaintext learner'
    Description       = 'Vigil - Windows telemetry triage and hunt (Track 13 spine tool). v0.6: SecretManagement-backed config, constrained remoting, and a Vigil.ReadOnly JEA role.'
    PowerShellVersion = '7.4'
    # Explicit exports are the module boundary - never use '*'.
    FunctionsToExport = @('Get-VigilEvent', 'Get-VigilConfig', 'Set-VigilSecret', 'Invoke-VigilRemote')
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
    # Declared as a dependency, not auto-loaded, so the module imports on Linux without a hard failure
    # if the Secret modules are absent; the config helpers require them at call time.
    RequiredModules   = @()
    PrivateData = @{
        PSData = @{
            Tags       = @('security', 'dfir', 'threat-hunting', 'secretmanagement', 'jea', 'least-privilege')
            ProjectUri = 'https://github.com/plaintext-security/plaintext-labs'
        }
    }
}
