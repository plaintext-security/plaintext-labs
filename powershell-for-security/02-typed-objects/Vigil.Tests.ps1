# Pester v5 tests for the reference Vigil module (Module 02). `make demo` runs these on a clean runner to
# prove the toolchain works and that ConvertTo-VigilEvent emits typed objects and rejects bad input.
# Your own function should grow tests alongside these.

Describe 'ConvertTo-VigilEvent' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:events = ConvertTo-VigilEvent -Path "$PSScriptRoot/data/raw-events.json" `
            -WarningAction SilentlyContinue
    }

    It 'emits objects, not strings' {
        $script:events[0] | Should -BeOfType ([VigilEvent])
    }

    It 'declares [VigilEvent] as its output type' {
        $ot = (Get-Command ConvertTo-VigilEvent).OutputType.Name
        $ot | Should -Contain 'VigilEvent'
    }

    It 'returns one object per VALID record (the malformed one is skipped)' {
        # raw-events.json has 8 records; the last is missing its Level field and is skipped.
        $script:events.Count | Should -Be 7
    }

    It 'coerces the string Id field to a real [int]' {
        $script:events[0].Id | Should -BeOfType ([int])
    }

    It 'coerces TimeCreated to a real [datetime]' {
        $script:events[0].TimeCreated | Should -BeOfType ([datetime])
    }

    It 'flags exactly the suspicious events in the sample' {
        # Three attacker-ish events: the IEX download cradle, the -enc/hidden launch, the FromBase64String block.
        ($script:events | Where-Object Suspicious).Count | Should -Be 3
    }

    It 'does not flag a benign Get-Process scriptblock' {
        $benign = $script:events | Where-Object { $_.Message -match 'Sort-Object CPU' }
        $benign.Suspicious | Should -BeFalse
    }

    It 'filters to a single known Level when -Level is supplied' {
        $warnings = ConvertTo-VigilEvent -Path "$PSScriptRoot/data/raw-events.json" -Level Warning `
            -WarningAction SilentlyContinue
        ($warnings | Where-Object { $_.Level -ne 'Warning' }).Count | Should -Be 0
    }

    It 'rejects an empty path at the boundary (parameter validation)' {
        { ConvertTo-VigilEvent -Path '' } | Should -Throw
    }

    It 'rejects a non-existent path at the boundary (parameter validation)' {
        { ConvertTo-VigilEvent -Path './does-not-exist.json' } | Should -Throw
    }

    It 'rejects an unknown -Level value (ValidateSet)' {
        { ConvertTo-VigilEvent -Path "$PSScriptRoot/data/raw-events.json" -Level 'Critical' } | Should -Throw
    }
}

Describe 'Get-VigilEvent (carried forward from Module 01)' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:legacy = Get-VigilEvent -Path "$PSScriptRoot/data/raw-events.json"
    }

    It 'still emits objects, not strings' {
        $script:legacy[0] | Should -BeOfType ([pscustomobject])
    }

    It 'is still exported by the module' {
        (Get-Command -Module Vigil).Name | Should -Contain 'Get-VigilEvent'
    }
}
