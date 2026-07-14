FROM mcr.microsoft.com/powershell:7.4-ubuntu-22.04

WORKDIR /lab

# Install the module toolchain plus the secrets stack, all pinned.
#   PSScriptAnalyzer / Pester            - lint + test gate (as in Module 01)
#   Microsoft.PowerShell.SecretManagement - the vault-abstraction cmdlets
#   Microsoft.PowerShell.SecretStore      - the cross-platform local vault (works in this Linux container)
# The Secret* modules are feature-complete/archived upstream; the pinned versions below are the
# latest published and are what production hosts use today.
RUN pwsh -NoProfile -Command "Set-PSResourceRepository PSGallery -Trusted; \
    Install-PSResource -Name PSScriptAnalyzer -Version 1.22.0 -TrustRepository; \
    Install-PSResource -Name Pester -Version 5.6.1 -TrustRepository; \
    Install-PSResource -Name Microsoft.PowerShell.SecretManagement -Version 1.1.2 -TrustRepository; \
    Install-PSResource -Name Microsoft.PowerShell.SecretStore -Version 1.0.6 -TrustRepository"

COPY . /lab

CMD ["pwsh", "-NoLogo", "-Command", "Start-Sleep -Seconds 2147483647"]
