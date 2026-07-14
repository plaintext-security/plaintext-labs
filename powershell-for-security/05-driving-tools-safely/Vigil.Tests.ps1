# Pester v5 tests for the reference Vigil module (Module 05).
# These PROVE the security property: a malicious argument fed to Invoke-VigilTool is treated as
# DATA, not executed - and the AST gate catches Invoke-Expression. `make demo` runs these on a
# clean runner.

BeforeAll {
    Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
    $script:tool = "$PSScriptRoot/data/vigil-scan.sh"
    $script:marker = Join-Path ([System.IO.Path]::GetTempPath()) 'vigil-pwned-marker'
}

Describe 'Invoke-VigilTool - injection safety' {

    BeforeEach {
        # Ensure a clean slate: the marker must NOT exist before each test.
        Remove-Item -Path $script:marker -Force -ErrorAction SilentlyContinue
    }

    It 'treats a shell-metacharacter filename as a single inert argument' {
        # This is THE proof: if the wrapper built a command string, the ';' would split it and the
        # second command would run. With an argument array, the whole thing is one argv token.
        $hostileArg = "evil.txt; touch $script:marker"
        $result = Invoke-VigilTool -FilePath $script:tool -ArgumentList @($hostileArg)

        # The injected `touch` must NOT have run.
        Test-Path -Path $script:marker | Should -BeFalse
        # The mock tool echoes exactly one argument, verbatim - proving it arrived as data.
        $result.StdOut.Trim() | Should -Be ("ARG[1]={0}" -f $hostileArg)
    }

    It 'treats a command-substitution filename as data' {
        $hostileArg = '$(touch ' + $script:marker + ')'
        $result = Invoke-VigilTool -FilePath $script:tool -ArgumentList @($hostileArg)

        Test-Path -Path $script:marker | Should -BeFalse
        $result.StdOut.Trim() | Should -Be ("ARG[1]={0}" -f $hostileArg)
    }

    It 'passes multiple arguments as discrete tokens' {
        $result = Invoke-VigilTool -FilePath $script:tool -ArgumentList @('a.txt', 'b.txt')
        $lines = ($result.StdOut.Trim() -split "`r?`n").Trim()
        $lines.Count | Should -Be 2
        $lines[0] | Should -Be 'ARG[1]=a.txt'
        $lines[1] | Should -Be 'ARG[2]=b.txt'
    }

    It 'returns a typed object with a real exit code' {
        $result = Invoke-VigilTool -FilePath $script:tool -ArgumentList @('clean.txt')
        $result | Should -BeOfType ([pscustomobject])
        $result.ExitCode | Should -Be 0
        $result.Success | Should -BeTrue
    }

    It 'surfaces a non-zero exit code as Success = $false' {
        # The mock tool returns exit 1 when any arg contains MATCH (a simulated "finding").
        $result = Invoke-VigilTool -FilePath $script:tool -ArgumentList @('MATCH-me.bin')
        $result.ExitCode | Should -Be 1
        $result.Success | Should -BeFalse
    }

    It 'rejects a non-existent tool path (parameter validation)' {
        { Invoke-VigilTool -FilePath './does-not-exist.sh' -ArgumentList @('x') } | Should -Throw
    }

    AfterEach {
        Remove-Item -Path $script:marker -Force -ErrorAction SilentlyContinue
    }
}

Describe 'Test-VigilNoInvokeExpression - the AST review gate' {

    It 'passes the clean Vigil module (no Invoke-Expression anywhere)' {
        Test-VigilNoInvokeExpression -Path "$PSScriptRoot/Vigil" | Should -BeTrue
    }

    It 'catches a planted Invoke-Expression in a script' {
        $dirty = Join-Path ([System.IO.Path]::GetTempPath()) 'vigil-dirty.ps1'
        # Build the banned call at runtime so this test file itself stays clean of the literal.
        $iex = 'Invoke-' + 'Expression'
        Set-Content -Path $dirty -Value "$iex `"Get-Process`"" -Encoding ascii
        try {
            Test-VigilNoInvokeExpression -Path $dirty -WarningAction SilentlyContinue |
                Should -BeFalse
        }
        finally {
            Remove-Item -Path $dirty -Force -ErrorAction SilentlyContinue
        }
    }

    It 'is NOT fooled by the word iex appearing only in a comment' {
        $commentOnly = Join-Path ([System.IO.Path]::GetTempPath()) 'vigil-comment.ps1'
        Set-Content -Path $commentOnly -Encoding ascii -Value @(
            '# This comment mentions Invoke-Expression and iex but invokes neither.',
            'Get-Date'
        )
        try {
            Test-VigilNoInvokeExpression -Path $commentOnly | Should -BeTrue
        }
        finally {
            Remove-Item -Path $commentOnly -Force -ErrorAction SilentlyContinue
        }
    }
}
