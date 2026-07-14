FROM mcr.microsoft.com/powershell:7.4-ubuntu-22.04

WORKDIR /lab

# openssl for the code-signing loop (Set-AuthenticodeSignature is Windows-only; see Module 09).
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

# The module toolchain, PINNED - the same versions the track gated on.
RUN pwsh -NoProfile -Command "Set-PSResourceRepository PSGallery -Trusted; \
    Install-PSResource -Name PSScriptAnalyzer -Version 1.22.0 -TrustRepository; \
    Install-PSResource -Name Pester -Version 5.6.1 -TrustRepository"

COPY . /lab

CMD ["pwsh", "-NoLogo", "-Command", "Start-Sleep -Seconds 2147483647"]
