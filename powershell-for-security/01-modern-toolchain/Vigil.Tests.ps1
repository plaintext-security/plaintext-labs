# Pester v5 tests for the reference Vigil module. `make demo` runs these on a clean runner
# to prove the toolchain works; your migration should grow its own tests alongside these.

Describe 'Get-VigilEvent' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:events = Get-VigilEvent -Path "$PSScriptRoot/data/sample.json"
    }

    It 'emits objects, not strings' {
        $script:events[0] | Should -BeOfType ([pscustomobject])
    }

    It 'returns one object per input event' {
        $script:events.Count | Should -Be 7
    }

    It 'flags exactly the suspicious events in the sample' {
        # Sample has three attacker-ish events: the IEX download cradle, the -enc/hidden
        # process launch, and the FromBase64String scriptblock.
        ($script:events | Where-Object Suspicious).Count | Should -Be 3
    }

    It 'does not flag a benign Get-Process scriptblock' {
        $benign = $script:events | Where-Object { $_.Message -match 'Sort-Object CPU' }
        $benign.Suspicious | Should -BeFalse
    }

    It 'rejects a non-existent path (parameter validation)' {
        { Get-VigilEvent -Path './does-not-exist.json' } | Should -Throw
    }
}
