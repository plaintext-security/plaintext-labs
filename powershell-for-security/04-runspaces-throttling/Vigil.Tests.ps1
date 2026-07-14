# Pester v5 tests for the reference Vigil module. `make demo` runs these on a clean
# runner to prove the enrichment works offline against the bundled feed snapshot.
# Your enrichment should grow its own tests alongside these.

Describe 'Get-VigilEvent' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:events = Get-VigilEvent -Path "$PSScriptRoot/data/sample.json" -ErrorAction SilentlyContinue
    }

    It 'still loads (cumulative module - the prior cmdlet is exported)' {
        (Get-Command -Module Vigil -Name Get-VigilEvent) | Should -Not -BeNullOrEmpty
    }
}

Describe 'Invoke-VigilEnrichment' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        $script:feed  = "$PSScriptRoot/data/feodo_ipblocklist.csv"
        $script:events = Get-Content "$PSScriptRoot/data/events.json" -Raw | ConvertFrom-Json
        $script:ips    = $script:events | ForEach-Object { $_.DestinationIp }
        $script:result = $script:ips | Invoke-VigilEnrichment -FeedPath $script:feed -ThrottleLimit 4
    }

    It 'emits objects, not strings' {
        $script:result[0] | Should -BeOfType ([pscustomobject])
    }

    It 'de-duplicates: one result per UNIQUE indicator (no lost or duplicated rows)' {
        # events.json has 10 events but only 9 unique destination IPs (one repeats).
        # A ConcurrentBag with $using: keeps every result; a racy += would drop some.
        $script:result.Count | Should -Be 9
        ($script:result.Indicator | Sort-Object -Unique).Count | Should -Be 9
    }

    It 'flags exactly the malicious indicators present in the feed snapshot' {
        # 5 of the destination IPs are documented-malware C2 IPs in the snapshot.
        ($script:result | Where-Object Malicious).Count | Should -Be 5
    }

    It 'does not flag a benign indicator' {
        $benign = $script:result | Where-Object { $_.Indicator -eq '142.250.72.196' }
        $benign.Malicious | Should -BeFalse
    }

    It 'attaches malware and c2 status from the feed to a malicious hit' {
        $hit = $script:result | Where-Object { $_.Indicator -eq '185.220.101.7' }
        $hit.Malicious | Should -BeTrue
        $hit.Malware   | Should -Be 'Emotet'
        $hit.C2Status  | Should -Be 'online'
    }

    It 'succeeds on the first attempt against the local snapshot (no spurious retries)' {
        ($script:result | Where-Object { $_.Attempts -ne 1 }) | Should -BeNullOrEmpty
    }

    It 'accepts indicators as a positional/pipeline array and by parameter' {
        $direct = Invoke-VigilEnrichment -Indicator '185.220.101.7', '8.8.8.8' -FeedPath $script:feed
        $direct.Count | Should -Be 2
        ($direct | Where-Object Malicious).Count | Should -Be 1
    }

    It 'rejects an invalid ThrottleLimit (parameter validation)' {
        { Invoke-VigilEnrichment -Indicator '8.8.8.8' -FeedPath $script:feed -ThrottleLimit 0 } |
            Should -Throw
    }

    It 'rejects a non-existent feed path (parameter validation)' {
        { Invoke-VigilEnrichment -Indicator '8.8.8.8' -FeedPath './nope.csv' } | Should -Throw
    }
}
