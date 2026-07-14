# Capstone Pester test stub. These are the SHAPES your suite must fill - real tests with
# mocks and unhappy paths, not a replay of a demo. Replace the Set-ItResult -Pending lines
# with real assertions as you implement each function. The rubric's "Tests & eval" dimension
# is graded on THIS file plus eval.ps1.

BeforeAll {
    Import-Module "$PSScriptRoot/../Vigil/Vigil.psd1" -Force
}

Describe 'Vigil module contract' {
    It 'exports exactly the intended public functions (explicit, never *)' {
        $exported = (Get-Command -Module Vigil).Name | Sort-Object
        $expected = 'ConvertTo-VigilEvent', 'Get-VigilDetection', 'Get-VigilEvent', 'Invoke-VigilEnrichment'
        $exported | Should -Be $expected
    }
}

Describe 'ConvertTo-VigilEvent (typed boundary)' {
    It 'emits a typed object, not a string' -Pending {
        # TODO: assert the output is [pscustomobject] with the fields your VigilEvent contract declares.
        Set-ItResult -Pending -Because 'implement ConvertTo-VigilEvent, then assert typed output'
    }

    It 'rejects malformed input at the boundary (unhappy path)' -Pending {
        Set-ItResult -Pending -Because 'assert bad input throws / is rejected by validation'
    }
}

Describe 'Invoke-VigilEnrichment (concurrency + mocked edge)' {
    It 'queries the feed once per unique indicator (Should -Invoke mock)' -Pending {
        # TODO: Mock the feed read (-ModuleName Vigil) and assert Should -Invoke -Times 1 -Exactly.
        Set-ItResult -Pending -Because 'mock the feed edge and assert invoke count'
    }
}

Describe 'Get-VigilDetection (the classifier under eval)' {
    It 'classifies a known-malicious sample as malicious' -Pending {
        Set-ItResult -Pending -Because 'implement the detection, then assert on a labelled sample'
    }
}
