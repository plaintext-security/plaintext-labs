# Small reusable tradecraft helpers, dot-sourced by demo.ps1. This is the starter you
# extend in the lab's "Automate & own it" step — AI can draft more transforms; you review
# every line and own what it emits. Nothing here is novel or weaponised: it is the same
# language-level encoding/obfuscation every defender must recognise on sight, shown so the
# blue-team module (Defensive 13) has something concrete to hunt.

function New-EncodedCommand {
    # The -EncodedCommand form: UTF-16LE bytes, Base64. This is what an analyst sees as
    # `powershell.exe -enc <blob>` on a command line — opaque until you decode it.
    param([Parameter(Mandatory)][string]$Command)
    [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
}

function ConvertFrom-EncodedCommand {
    # Decode an -enc blob back to source. The point of the lab: this is trivial, so the
    # encoding buys nothing against a defender who knows the form.
    param([Parameter(Mandatory)][string]$Encoded)
    [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($Encoded))
}

function New-ObfuscatedCommand {
    # Behaviour-preserving obfuscation: split the command into characters and rebuild it
    # at runtime with -join. Different bytes, identical behaviour — defeats a naive string
    # signature but NOT runtime script-block logging, which records the rebuilt text.
    param([Parameter(Mandatory)][string]$Command)
    $chars = $Command.ToCharArray() | ForEach-Object { "[char]$([int][char]$_)" }
    $expr = $chars -join '+'
    "& ([scriptblock]::Create($expr))"
}

function New-ScriptBlockLogRecord {
    # Emit the Event ID 4104 record (Microsoft-Windows-PowerShell/Operational) that this
    # command WOULD generate when script-block logging is on. The defensive module hunts
    # exactly this shape — note ScriptBlockText holds the *deobfuscated* command.
    param(
        [Parameter(Mandatory)][string]$ScriptBlockText,
        [string]$User = 'CORP\jsmith',
        [string]$ComputerName = 'FIN-WKSTN-07'
    )
    [pscustomobject]@{
        TimeCreated     = (Get-Date).ToString('o')
        Id              = 4104
        LogName         = 'Microsoft-Windows-PowerShell/Operational'
        Level           = 'Warning'
        Computer        = $ComputerName
        UserId          = $User
        ScriptBlockText = $ScriptBlockText
    }
}
