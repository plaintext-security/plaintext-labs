FROM mcr.microsoft.com/powershell:7.4-ubuntu-22.04

WORKDIR /lab

# openssl is used by sign.ps1 to mint a self-signed code-signing cert on Linux (there is
# no New-SelfSignedCertificate on pwsh/Linux). Present on the base image; installed here to
# be explicit and to keep the build reproducible.
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

# Install the module toolchain: PSScriptAnalyzer (lint) + Pester (test), PINNED.
# An unpinned install makes the gate that measures the module irreproducible.
RUN pwsh -NoProfile -Command "Set-PSResourceRepository PSGallery -Trusted; \
    Install-PSResource -Name PSScriptAnalyzer -Version 1.22.0 -TrustRepository; \
    Install-PSResource -Name Pester -Version 5.6.1 -TrustRepository"

COPY . /lab

CMD ["pwsh", "-NoLogo", "-Command", "Start-Sleep -Seconds 2147483647"]
