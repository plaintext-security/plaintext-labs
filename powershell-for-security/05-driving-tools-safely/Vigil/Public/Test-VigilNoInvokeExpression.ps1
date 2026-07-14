function Test-VigilNoInvokeExpression {
    <#
    .SYNOPSIS
        AST review gate: fails if any .ps1 under a path invokes Invoke-Expression / iex.
    .DESCRIPTION
        Parses each script into its abstract syntax tree with the PowerShell language Parser and
        walks it for CommandAst nodes whose command name is Invoke-Expression or its alias iex.
        Because it inspects the parsed tree (not raw text), the word appearing in a comment or a
        string literal does NOT trip it - only a real command invocation does. This is the review
        gate that makes 'no Invoke-Expression in Vigil' a build failure instead of a hope.
    .PARAMETER Path
        A file or directory to scan (directories are scanned recursively for *.ps1).
    .EXAMPLE
        if (Test-VigilNoInvokeExpression -Path ./Vigil) { 'clean' } else { throw 'iex found' }
    .OUTPUTS
        System.Boolean - $true when clean, $false when a banned invocation is found (each finding is
        written as a warning: file, line, and command name).
    #>
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ })]
        [string]$Path
    )

    $banned = @('Invoke-Expression', 'iex')

    $files = if (Test-Path -Path $Path -PathType Container) {
        Get-ChildItem -Path $Path -Recurse -Filter '*.ps1' -File
    }
    else {
        Get-Item -Path $Path
    }

    $findings = foreach ($file in $files) {
        $tokens = $null
        $errors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            $file.FullName, [ref]$tokens, [ref]$errors)

        $commands = $ast.FindAll({
                param($node)
                $node -is [System.Management.Automation.Language.CommandAst] -and
                $banned -contains $node.GetCommandName()
            }, $true)

        foreach ($cmd in $commands) {
            [pscustomobject]@{
                File    = $file.Name
                Line    = $cmd.Extent.StartLineNumber
                Command = $cmd.GetCommandName()
            }
        }
    }

    if ($findings) {
        foreach ($f in $findings) {
            Write-Warning ("Banned invocation: {0}:{1} ({2})" -f $f.File, $f.Line, $f.Command)
        }
        return $false
    }

    return $true
}
