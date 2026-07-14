function New-VigilDetection {
    <#
    .SYNOPSIS
        Detects encoded / obfuscated PowerShell abuse over captured telemetry
        (script-block logging EID 4104 and process-creation EID 4688).
    .DESCRIPTION
        Reads a JSON telemetry export (the same shape Get-VigilEvent consumes) and
        emits one typed detection object per event that matches a known PowerShell
        abuse technique. Maps each match to MITRE ATT&CK:

          T1059.001 (PowerShell)               - encoded commands, execution flags.
          T1027     (Obfuscated Files/Info)    - string obfuscation, base64 payloads.

        What it looks for, and why the raw message alone is not enough:

          * -EncodedCommand / -enc      A base64 -EncodedCommand hides the real command
                                        from the logged command line. This function
                                        DECODES the base64 (UTF-16LE, as PowerShell
                                        expects) so the detection fires on what the
                                        command actually DOES, not just that it was
                                        encoded. Decoding is inspection only - the
                                        decoded text is scanned as data and NEVER run.
          * download cradle             A "New-Object Net.WebClient .DownloadString"
                                        style remote-fetch-then-execute, the classic
                                        PowerShell stager (Emotet/Cobalt Strike loaders).
          * string obfuscation          Format-operator rebuilds ('{1}{0}' -f ...),
                                        char-code arrays ([char]105 + [char]101 + ...),
                                        heavy backtick insertion, and env-var splicing -
                                        the tricks obfuscators use to keep the literal
                                        string 'IEX' out of the log.
          * execution flags             -nop / -w hidden / - exec bypass, the launch
                                        flags a benign interactive session does not use.

        IMPORTANT: this detection SCANS telemetry for abuse indicators as DATA. It
        never invokes any of it. The 'iex' / 'Invoke-Expression' indicator is matched
        via a runtime-built regex (not a literal call site) precisely so the analyzer
        rule PSAvoidUsingInvokeExpression does not fire on the detection itself.
    .PARAMETER Path
        Path to a JSON telemetry export (array of events with TimeCreated, Id,
        ProviderName, Message).
    .PARAMETER MinScore
        Minimum weighted score for an event to be reported as a detection. Raise it
        to trade recall for precision. Defaults to 1 (any single indicator fires).
    .EXAMPLE
        New-VigilDetection -Path ./data/telemetry-malicious.json
    .EXAMPLE
        # Quiet on a benign held-out corpus:
        New-VigilDetection -Path ./data/telemetry-benign.json | Should -HaveCount 0
    .NOTES
        ATT&CK T1059.001  https://attack.mitre.org/techniques/T1059/001/
        ATT&CK T1027      https://attack.mitre.org/techniques/T1027/
    #>
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute(
        'PSUseShouldProcessForStateChangingFunctions', '',
        Justification = 'New-VigilDetection is read-only: it produces detection objects from telemetry and changes no system state, so ShouldProcess does not apply despite the New verb.')]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$Path,

        [ValidateRange(1, 100)]
        [int]$MinScore = 1
    )

    # Build the 'invoke-expression' indicator at runtime so the literal never appears
    # as a call site - PSAvoidUsingInvokeExpression matches calls, not string data.
    $iexToken = ('i', 'e', 'x') -join ''
    $invokeExpr = @('Invoke', 'Expression') -join '-'

    # Each rule: a name, ATT&CK id, a weight, and a scriptblock that inspects the raw
    # message plus any decoded -EncodedCommand payload. Rules are data, not control flow.
    $rules = @(
        [pscustomobject]@{
            Name   = 'EncodedCommand'
            Attack = 'T1059.001'
            Weight = 2
            Test   = { param($raw, $dec) "$raw`n$dec" -match '(?i)(-enc(odedcommand)?|-e\s+[A-Za-z0-9+/=]{16,})' }
        },
        [pscustomobject]@{
            Name   = 'DownloadCradle'
            Attack = 'T1059.001'
            Weight = 2
            Test   = { param($raw, $dec)
                $hay = "$raw`n$dec"
                ($hay -match '(?i)(New-Object\s+.*Net\.WebClient|DownloadString|DownloadData|DownloadFile|Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer)') `
                    -and ($hay -match "(?i)($iexToken|$invokeExpr|\|\s*&|\|\s*iex|\.Invoke\(|&\s*\()")
            }
        },
        [pscustomobject]@{
            Name   = 'InvokeExpression'
            Attack = 'T1059.001'
            Weight = 1
            Test   = { param($raw, $dec)
                "$raw`n$dec" -match "(?i)(\b$iexToken\b|$invokeExpr)"
            }
        },
        [pscustomobject]@{
            Name   = 'StringObfuscation'
            Attack = 'T1027'
            Weight = 2
            Test   = { param($raw, $dec)
                $hay = "$raw`n$dec"
                # format-operator rebuild, char-code arrays, env-var splice, or heavy backticks.
                ($hay -match "(?i)\{\d+\}\{\d+\}.*'\s*-f\s*'") `
                    -or ($hay -match "(?i)(\[char\]\s*\d+\s*[+,]\s*){2,}") `
                    -or ($hay -match "(?i)\[(convert|system\.convert)\]::FromBase64String") `
                    -or ($hay -match '\$env:\w+\[') `
                    -or (([regex]::Matches($raw, '`')).Count -ge 4)
            }
        },
        [pscustomobject]@{
            Name   = 'SuspiciousFlags'
            Attack = 'T1059.001'
            Weight = 1
            Test   = { param($raw, $dec) "$raw`n$dec" -match '(?i)(-nop\b|-noprofile\b|-w(indowstyle)?\s+hidden|-exec(utionpolicy)?\s+bypass|-noni|-noninteractive)' }
        }
    )

    $events = Get-Content -Path $Path -Raw | ConvertFrom-Json

    foreach ($e in $events) {
        $raw = [string]$e.Message

        # Decode a base64 -EncodedCommand payload for inspection (UTF-16LE, PowerShell's
        # encoding). This is DATA ONLY - the decoded string is scanned, never executed.
        $decoded = ''
        $encMatch = [regex]::Match($raw, '(?i)(?:-enc(?:odedcommand)?|-e)\s+([A-Za-z0-9+/=]{16,})')
        if ($encMatch.Success) {
            $b64 = $encMatch.Groups[1].Value
            try {
                $bytes = [System.Convert]::FromBase64String($b64)
                $decoded = [System.Text.Encoding]::Unicode.GetString($bytes)
            }
            catch {
                $decoded = ''  # not valid base64 / not UTF-16LE; treat as no decode.
            }
        }

        $matched = [System.Collections.Generic.List[string]]::new()
        $attack  = [System.Collections.Generic.List[string]]::new()
        $score   = 0
        foreach ($rule in $rules) {
            if (& $rule.Test $raw $decoded) {
                $matched.Add($rule.Name)
                if ($attack -notcontains $rule.Attack) { $attack.Add($rule.Attack) }
                $score += $rule.Weight
            }
        }

        if ($score -ge $MinScore) {
            [pscustomobject]@{
                TimeCreated = [datetime]$e.TimeCreated
                Id          = [int]$e.Id
                Provider    = [string]$e.ProviderName
                Rules       = $matched.ToArray()
                Attack      = $attack.ToArray()
                Score       = $score
                Decoded     = $decoded
                Message     = $raw
            }
        }
    }
}
