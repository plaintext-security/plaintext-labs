# Pester v5 tests for the reference Vigil module (M08 detection).
# `make demo` runs these on a clean runner to prove the detection FIRES on the
# malicious telemetry sample and is QUIET on the benign held-out sample.

Describe 'New-VigilDetection' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:mal    = New-VigilDetection -Path "$PSScriptRoot/data/telemetry-malicious.json"
        $script:benign = New-VigilDetection -Path "$PSScriptRoot/data/telemetry-benign.json"
    }

    It 'fires on every malicious event in the sample' {
        # All five malicious events carry at least one abuse indicator.
        $script:mal.Count | Should -Be 5
    }

    It 'is QUIET on the benign held-out sample (no false positives)' {
        @($script:benign).Count | Should -Be 0
    }

    It 'emits typed objects, not strings' {
        $script:mal[0] | Should -BeOfType ([pscustomobject])
    }

    It 'decodes a base64 -EncodedCommand and detects the cradle inside it' {
        $enc = $script:mal | Where-Object { $_.Rules -contains 'EncodedCommand' } | Select-Object -First 1
        $enc | Should -Not -BeNullOrEmpty
        # The decoded payload must be surfaced and must reveal the download cradle.
        $enc.Decoded | Should -Match 'DownloadString'
        $enc.Rules | Should -Contain 'DownloadCradle'
    }

    It 'maps detections to the right ATT&CK techniques' {
        $script:mal.Attack | Should -Contain 'T1059.001'
        ($script:mal | Where-Object { $_.Rules -contains 'StringObfuscation' }).Attack |
            Should -Contain 'T1027'
    }

    It 'catches format-operator obfuscation that hides the literal IEX string' {
        $obf = $script:mal | Where-Object { $_.Message -match "\{1\}\{0\}'-f'X','IE'" }
        $obf | Should -Not -BeNullOrEmpty
        $obf.Rules | Should -Contain 'StringObfuscation'
    }

    It 'MinScore raises precision (fewer, higher-confidence detections)' {
        $strict = New-VigilDetection -Path "$PSScriptRoot/data/telemetry-malicious.json" -MinScore 3
        $strict.Count | Should -BeLessOrEqual $script:mal.Count
        $strict | ForEach-Object { $_.Score | Should -BeGreaterOrEqual 3 }
    }

    It 'rejects a non-existent path (parameter validation)' {
        { New-VigilDetection -Path './does-not-exist.json' } | Should -Throw
    }
}

Describe 'Vigil module surface' {
    BeforeAll { Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force }

    It 'exports the cumulative cmdlet set through M08' {
        $exported = (Get-Command -Module Vigil).Name
        $exported | Should -Contain 'Get-VigilEvent'
        $exported | Should -Contain 'Invoke-VigilEnrichment'
        $exported | Should -Contain 'New-VigilDetection'
    }
}
