FROM mcr.microsoft.com/powershell:7.4-ubuntu-22.04

WORKDIR /lab

# Install the module toolchain: PSScriptAnalyzer (lint) + Pester (test), pinned.
RUN pwsh -NoProfile -Command "Set-PSResourceRepository PSGallery -Trusted; \
    Install-PSResource -Name PSScriptAnalyzer -Version 1.22.0 -TrustRepository; \
    Install-PSResource -Name Pester -Version 5.6.1 -TrustRepository"

COPY . /lab

CMD ["pwsh", "-NoLogo", "-Command", "Start-Sleep -Seconds 2147483647"]
