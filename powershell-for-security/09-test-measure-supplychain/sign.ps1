#!/usr/bin/env pwsh
# sign.ps1 - the supply-chain signing loop: mint a code-signing cert, SIGN the module,
# VERIFY before trust, and prove TAMPERING is caught. Runs offline in the Linux container.
#
# IMPORTANT - the Windows tool vs. what the Linux container can demonstrate:
#   On Windows the loop is:
#       $c = New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=Vigil'
#       Set-AuthenticodeSignature -FilePath ./Vigil/Vigil.psm1 -Certificate $c
#       (Get-AuthenticodeSignature ./Vigil/Vigil.psm1).Status   # -> Valid
#   Set-/Get-AuthenticodeSignature are WINDOWS-ONLY cmdlets - they are NOT present on
#   Linux/pwsh (Microsoft.PowerShell.Security only ships the CMS/credential cmdlets there).
#   So the Authenticode cmdlet loop is ASSESSED-NOT-DEMONSTRATED in this container.
#
#   To DEMONSTRATE the identical PRIMITIVE offline on Linux, we use openssl CMS - the exact
#   PKCS#7/CMS signature construct Authenticode is built on: a detached signature over the
#   module made with a code-signing cert, verified against that cert, and shown to REJECT a
#   tampered file. Same mechanism (sign -> verify-before-trust -> reject-on-tamper); only the
#   Windows-specific cmdlet + full chain-trust need a Windows host.

[CmdletBinding()]
param(
    [string]$SourceModule = "$PSScriptRoot/Vigil",
    [string]$WorkDir      = "$PSScriptRoot/.sign"
)

$ErrorActionPreference = 'Stop'

# Work on a COPY so signing / the deliberate tamper never mutate the source, keeping `make demo` idempotent.
if (Test-Path $WorkDir) { Remove-Item -Path $WorkDir -Recurse -Force }
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
$ModulePath = Join-Path $WorkDir 'Vigil'
Copy-Item -Path $SourceModule -Destination $ModulePath -Recurse -Force

$keyPath = Join-Path $WorkDir 'codesign.key'
$crtPath = Join-Path $WorkDir 'codesign.crt'
$extConf = Join-Path $WorkDir 'codesign.cnf'

Write-Output '=== 1. Mint a self-signed CODE-SIGNING certificate (openssl) ==='
# extendedKeyUsage=codeSigning is what makes this a code-signing cert, not a TLS cert -
# the same EKU Set-AuthenticodeSignature requires of the cert you hand it.
@'
[req]
distinguished_name = dn
prompt = no
[dn]
CN = Vigil Lab Signing
[v3]
keyUsage = digitalSignature
extendedKeyUsage = codeSigning
'@ | Set-Content -Path $extConf

& openssl req -x509 -newkey rsa:2048 -nodes -keyout $keyPath -out $crtPath `
    -days 365 -config $extConf -extensions v3 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error 'openssl cert generation failed.' }
Write-Output 'Cert: CN=Vigil Lab Signing (extendedKeyUsage=codeSigning)'
Write-Output ''

Write-Output '=== 2. Sign every module file (detached CMS/PKCS#7 signature) ==='
$files = Get-ChildItem -Path $ModulePath -Recurse -Include '*.ps1', '*.psm1', '*.psd1'
foreach ($f in $files) {
    $sigFile = "$($f.FullName).p7s"
    & openssl cms -sign -binary -in $f.FullName -signer $crtPath -inkey $keyPath `
        -outform PEM -out $sigFile 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Error "Signing failed for $($f.Name)." }
    Write-Output "  signed $($f.Name) -> $($f.Name).p7s"
}
Write-Output ''

Write-Output '=== 3. Verify EVERY file against the signing cert (before trust) ==='
foreach ($f in $files) {
    $sigFile = "$($f.FullName).p7s"
    # -CAfile the signer + -no_check_time: we trust this self-signed cert as the root in the lab.
    & openssl cms -verify -binary -in $sigFile -inform PEM -content $f.FullName `
        -CAfile $crtPath -purpose any -out /dev/null 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Error "Signature verification FAILED for $($f.Name)." }
}
Write-Output "All $($files.Count) module files verify against the signing cert."
Write-Output ''

Write-Output '=== 4. Prove tampering is caught (flip a byte, re-verify -> must FAIL) ==='
$target  = ($files | Select-Object -First 1).FullName
$sigFile = "$target.p7s"
$raw     = Get-Content -Path $target -Raw
Set-Content -Path $target -Value ($raw + "`n# tampered by an attacker after signing") -NoNewline

& openssl cms -verify -binary -in $sigFile -inform PEM -content $target `
    -CAfile $crtPath -purpose any -out /dev/null 2>$null
$tamperVerified = ($LASTEXITCODE -eq 0)

if ($tamperVerified) {
    Write-Error 'Tampering was NOT detected - the signing loop is broken.'
}
Write-Output 'Tampering detected: the modified file no longer verifies against its signature.'
Write-Output 'Signing loop works: sign -> verify-before-trust -> reject-on-tamper.'
Write-Output '(On Windows the identical loop is Set-/Get-AuthenticodeSignature - Valid vs. HashMismatch.)'
