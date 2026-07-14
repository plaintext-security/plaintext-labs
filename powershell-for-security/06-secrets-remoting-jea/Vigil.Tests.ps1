# Pester v5 tests for the reference Vigil module (Module 06).
#
# What runs LIVE on Linux (in the container):
#   - SecretManagement + SecretStore: register a throwaway vault, Set/Get a secret through Vigil's
#     helpers. SecretStore is cross-platform, so this is a real end-to-end secret round-trip.
#   - The JEA .psrc / .pssc capability files: parsed with Import-PowerShellDataFile and shape-checked
#     (read-only surface, no wildcards, virtual account, RestrictedRemoteServer). Proves they are
#     well-formed and least-privilege. (Test-PSSessionConfigurationFile is Windows-only and is run on
#     the optional VM, not here.)
#
# What is NOT run on Linux (Windows-only, asserted for shape only, exercised on the optional VM):
#   - JEA *enforcement* and WinRM remoting. Invoke-VigilRemote is unit-checked for its guard and
#     parameter contract; it cannot open a real constrained session without a Windows host.
#
# The test vault is configured with -Authentication None -Interaction None. That is fine for a
# THROWAWAY test store holding a fake secret; NEVER do this for real secrets.

# Evaluated at DISCOVERY time (top-level) so the -Skip on the secret Describe resolves correctly -
# a variable set only inside BeforeAll is not visible when Pester evaluates -Skip during discovery.
$HaveSecretStack = [bool](
    (Get-Module -ListAvailable Microsoft.PowerShell.SecretManagement) -and
    (Get-Module -ListAvailable Microsoft.PowerShell.SecretStore))

BeforeAll {
    Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force

    # Recompute in run-phase scope (the discovery-time $HaveSecretStack is not visible here).
    $script:HaveSecretStack = [bool](
        (Get-Module -ListAvailable Microsoft.PowerShell.SecretManagement) -and
        (Get-Module -ListAvailable Microsoft.PowerShell.SecretStore))

    if ($script:HaveSecretStack) {
        Import-Module Microsoft.PowerShell.SecretManagement -Force
        Import-Module Microsoft.PowerShell.SecretStore -Force

        # Initialize a FRESH, passwordless store non-interactively. Reset-SecretStore creates the
        # store with -Authentication None so the first Set-Secret never prompts. No-password /
        # no-prompt is valid for a THROWAWAY test store holding a fake secret; NEVER for real secrets.
        # (In the disposable lab container this store is the container's alone; AfterAll unregisters
        #  the test vault so nothing lingers.)
        Reset-SecretStore -Scope CurrentUser -Authentication None -Interaction None `
            -Force -Confirm:$false -ErrorAction Stop

        Register-SecretVault -Name 'VigilTestStore' `
            -ModuleName Microsoft.PowerShell.SecretStore -DefaultVault -ErrorAction Stop
    }
}

AfterAll {
    if ($script:HaveSecretStack) {
        Unregister-SecretVault -Name 'VigilTestStore' -ErrorAction SilentlyContinue
    }
}

Describe 'Vigil module surface' {
    It 'exports exactly the four public functions' {
        $exported = (Get-Command -Module Vigil).Name | Sort-Object
        $exported | Should -Be @('Get-VigilConfig', 'Get-VigilEvent', 'Invoke-VigilRemote', 'Set-VigilSecret')
    }
}

Describe 'Secret round-trip through Vigil (SecretManagement + SecretStore)' -Skip:(-not $HaveSecretStack) {
    It 'stores a secret via Set-VigilSecret and reads it back via Get-Secret' {
        $plain  = 'not-a-real-token-{0}' -f ([guid]::NewGuid())
        $secure = ConvertTo-SecureString -String $plain -AsPlainText -Force

        Set-VigilSecret -Name 'vigil-feed-token' -Secret $secure -Vault 'VigilTestStore' -Confirm:$false

        $roundTrip = Get-Secret -Name 'vigil-feed-token' -Vault 'VigilTestStore' -AsPlainText
        $roundTrip | Should -Be $plain
    }

    It 'Get-VigilConfig resolves the secret lazily via GetToken()' {
        $plain  = 'lazy-token-{0}' -f ([guid]::NewGuid())
        $secure = ConvertTo-SecureString -String $plain -AsPlainText -Force
        Set-VigilSecret -Name 'vigil-feed-token' -Secret $secure -Vault 'VigilTestStore' -Confirm:$false

        $cfg = Get-VigilConfig -Path "$PSScriptRoot/data/vigil.config.json" -Vault 'VigilTestStore'

        $cfg.SecretName | Should -Be 'vigil-feed-token'
        $cfg.FeedUrl    | Should -Match '^https://'
        $cfg.GetToken() | Should -Be $plain
    }

    It 'Set-VigilSecret refuses a plaintext string (secure input only)' {
        # The parameter is [securestring]; a bare string cannot bind, so plaintext cannot flow through.
        { Set-VigilSecret -Name 'x' -Secret 'plaintext' -Vault 'VigilTestStore' -Confirm:$false } |
            Should -Throw
    }
}

Describe 'Vigil.ReadOnly JEA role capability (.psrc) is well-formed and read-only' {
    BeforeAll {
        $script:psrcPath = "$PSScriptRoot/Vigil/jea/Vigil.ReadOnly.psrc"
        # A .psrc is a PowerShell data file (a hashtable). Import it safely (no code execution).
        $script:psrc = Import-PowerShellDataFile -Path $script:psrcPath
    }

    It 'parses as a data file' {
        $script:psrc | Should -BeOfType ([hashtable])
    }

    It 'exposes only Vigil read-only hunt functions' {
        $script:psrc.VisibleFunctions | Should -Contain 'Get-VigilEvent'
        # No state-changing verbs slipped into the visible functions.
        foreach ($fn in $script:psrc.VisibleFunctions) {
            $fn | Should -Not -Match '^(Set|New|Remove|Invoke|Start|Stop|Register|Add|Clear)-'
        }
    }

    It 'declares no wildcard visible cmdlets (least privilege, per MS guidance)' {
        foreach ($c in $script:psrc.VisibleCmdlets) {
            $name = if ($c -is [hashtable]) { [string]$c.Name } else { [string]$c }
            $name | Should -Not -Match '\*'
        }
    }

    It 'exposes no providers or external commands' {
        $script:psrc.VisibleProviders        | Should -BeNullOrEmpty
        $script:psrc.VisibleExternalCommands | Should -BeNullOrEmpty
    }

    It 'imports the Vigil module so proxied verbs resolve' {
        $script:psrc.ModulesToImport | Should -Contain 'Vigil'
    }
}

Describe 'Vigil.ReadOnly JEA session configuration (.pssc) is well-formed and constrained' {
    BeforeAll {
        $script:psscPath = "$PSScriptRoot/Vigil/jea/Vigil.ReadOnly.pssc"
        $script:pssc = Import-PowerShellDataFile -Path $script:psscPath
    }

    It 'is a RestrictedRemoteServer session (NoLanguage, minimal defaults)' {
        $script:pssc.SessionType | Should -Be 'RestrictedRemoteServer'
    }

    It 'runs under a temporary virtual account, not a standing admin' {
        $script:pssc.RunAsVirtualAccount | Should -BeTrue
    }

    It 'maps a group to the Vigil.ReadOnly role capability' {
        $roles = $script:pssc.RoleDefinitions.Values.RoleCapabilities
        $roles | Should -Contain 'Vigil.ReadOnly'
    }

    It 'passes Test-PSSessionConfigurationFile (Windows-only; skipped on Linux)' {
        # Test-PSSessionConfigurationFile validates the .pssc syntax, but it is part of the Windows-only
        # remoting/JEA surface and is NOT present on Linux pwsh. On Linux we have already proved the file
        # is well-formed via Import-PowerShellDataFile + the shape assertions above; this extra check
        # runs on the optional Windows VM. Skip honestly rather than pretend it ran.
        $cmd = Get-Command Test-PSSessionConfigurationFile -ErrorAction SilentlyContinue
        if (-not $cmd) {
            Set-ItResult -Skipped -Because 'Test-PSSessionConfigurationFile is Windows-only (see lab.md VM step)'
            return
        }
        Test-PSSessionConfigurationFile -Path $script:psscPath | Should -BeTrue
    }
}

Describe 'Invoke-VigilRemote (Windows-only enforcement; shape-checked on Linux)' {
    It 'constrains -Command to the read-only verb whitelist' {
        # A verb outside the ValidateSet must not bind - you cannot ask the endpoint for anything else.
        $cred = [pscredential]::new('u', (ConvertTo-SecureString 'p' -AsPlainText -Force))
        { Invoke-VigilRemote -ComputerName 'DC01' -Command 'Remove-Item' -Credential $cred } |
            Should -Throw
    }

    It 'fails loudly on a non-Windows host instead of a confusing WinRM error' -Skip:($IsWindows) {
        $cred = [pscredential]::new('u', (ConvertTo-SecureString 'p' -AsPlainText -Force))
        { Invoke-VigilRemote -ComputerName 'DC01' -Command 'Get-VigilEvent' -Credential $cred } |
            Should -Throw -ExpectedMessage '*Windows host*'
    }
}
