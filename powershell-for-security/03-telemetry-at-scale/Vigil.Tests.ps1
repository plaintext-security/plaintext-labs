# Pester v5 tests for the reference Vigil module (v0.3). `make demo` runs these on a clean
# Linux runner to prove the toolchain works WITHOUT Get-WinEvent (Windows-only) - the events are
# parsed from a pre-exported evtx_dump JSONL artifact. Your lab work should grow its own tests here.

Describe 'Get-VigilEvent' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:data = "$PSScriptRoot/data/events.jsonl"
        $script:events = Get-VigilEvent -Path $script:data
    }

    It 'emits objects, not strings' {
        $script:events[0] | Should -BeOfType ([pscustomobject])
    }

    It 'returns one object per input event' {
        $script:events.Count | Should -Be 15
    }

    It 'normalizes TimeCreated to a datetime' {
        $script:events[0].TimeCreated | Should -BeOfType ([datetime])
    }

    It 'flags exactly the suspicious events in the sample' {
        ($script:events | Where-Object Suspicious).Count | Should -Be 7
    }

    It 'does not flag a benign Get-Process scriptblock' {
        $benign = $script:events | Where-Object { $_.CommandLine -match 'Sort-Object CPU' }
        $benign.Suspicious | Should -BeFalse
    }

    It 'rejects a non-existent path (parameter validation)' {
        { Get-VigilEvent -Path './does-not-exist.jsonl' } | Should -Throw
    }
}

Describe 'Get-VigilEvent source-side filtering' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:data = "$PSScriptRoot/data/events.jsonl"
    }

    It 'filters by EventId before emitting (server-side analogue)' {
        $only4104 = Get-VigilEvent -Path $script:data -EventId 4104
        ($only4104 | Where-Object { $_.EventId -ne 4104 }).Count | Should -Be 0
        $only4104.Count | Should -Be 5
    }

    It 'filters by Provider wildcard' {
        $sysmon = Get-VigilEvent -Path $script:data -Provider '*Sysmon*'
        ($sysmon | Where-Object { $_.Provider -notlike '*Sysmon*' }).Count | Should -Be 0
        $sysmon.Count | Should -Be 5
    }

    It 'combines EventId and Provider filters' {
        $ps4104 = Get-VigilEvent -Path $script:data -EventId 4104 -Provider '*PowerShell*'
        $ps4104.Count | Should -Be 5
    }
}

Describe 'Write-VigilLog' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
    }

    It 'emits one line of valid JSON, not a host string' {
        $line = Write-VigilLog -Message 'hello' -Level Info
        { $line | ConvertFrom-Json } | Should -Not -Throw
        ($line -split "`n").Count | Should -Be 1
    }

    It 'includes timestamp, level and message fields' {
        $obj = Write-VigilLog -Message 'hunt started' -Level Warning | ConvertFrom-Json
        $obj.level | Should -Be 'Warning'
        $obj.message | Should -Be 'hunt started'
        $obj.timestamp | Should -Not -BeNullOrEmpty
    }

    It 'merges extra structured Data fields' {
        $obj = Write-VigilLog -Message 'hit' -Level Warning -Data @{ EventId = 4104; Host = 'WKS07' } | ConvertFrom-Json
        $obj.EventId | Should -Be 4104
        $obj.Host | Should -Be 'WKS07'
    }

    It 'suppresses records below the minimum level' {
        $out = Write-VigilLog -Message 'noisy' -Level Debug -MinimumLevel Info
        $out | Should -BeNullOrEmpty
    }
}
