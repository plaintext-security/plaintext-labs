function Invoke-VigilTool {
    <#
    .SYNOPSIS
        Injection-safe wrapper for driving an external binary from Vigil.
    .DESCRIPTION
        Runs an external tool with caller-supplied arguments passed via the NATIVE CALL OPERATOR
        and array splatting (& $FilePath @ArgumentList) - never a string-built command line and
        never Invoke-Expression. Each argument reaches the process as a discrete argv token that no
        shell re-parses, so a hostile filename such as 'evil.txt; rm -rf /' is treated as DATA, not
        executed.

        (Note: & @args is used deliberately rather than Start-Process -ArgumentList. On .NET,
        Start-Process joins the argument list back into a single string that the runtime re-splits
        on whitespace - which would break a filename that legitimately contains spaces. The call
        operator preserves the argv array faithfully.)

        Captures stdout, stderr, and the process exit code, and returns a typed object so a failed
        tool and an empty result are distinguishable (ExitCode / Success), not a bare stdout blob.
    .EXAMPLE
        Invoke-VigilTool -FilePath ./data/vigil-scan.sh -ArgumentList @('evil.txt; rm -rf /')
        # The metacharacters are echoed back verbatim as a single argument - nothing runs.
    .OUTPUTS
        pscustomobject with Tool, ArgumentList, ExitCode, Success, StdOut, StdErr.
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$FilePath,

        # Arguments are passed to the process as an array of discrete tokens - the trust boundary.
        [string[]]$ArgumentList = @()
    )

    $errFile = New-TemporaryFile
    try {
        # The native call operator with splatting passes each element as a separate argv entry.
        # Redirect stderr (stream 2) to a temp file so it is captured separately from stdout.
        $stdout = & $FilePath @ArgumentList 2>$errFile.FullName
        $exitCode = $LASTEXITCODE

        $stderr = Get-Content -Path $errFile.FullName -Raw

        # Normalize stdout: & returns an array of lines; join back into a single string for parsing.
        $stdoutText = if ($null -eq $stdout) { '' } else { ($stdout -join [Environment]::NewLine) }

        [pscustomobject]@{
            Tool         = $FilePath
            ArgumentList = $ArgumentList
            ExitCode     = $exitCode
            Success      = ($exitCode -eq 0)
            StdOut       = $stdoutText
            StdErr       = if ($null -eq $stderr) { '' } else { $stderr }
        }
    }
    finally {
        Remove-Item -Path $errFile.FullName -Force -ErrorAction SilentlyContinue
    }
}
