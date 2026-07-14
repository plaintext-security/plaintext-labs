FROM mcr.microsoft.com/powershell:7.4-ubuntu-22.04

WORKDIR /lab

# Install the module toolchain: PSScriptAnalyzer (lint) + Pester (test), pinned.
RUN pwsh -NoProfile -Command "Set-PSResourceRepository PSGallery -Trusted; \
    Install-PSResource -Name PSScriptAnalyzer -Version 1.22.0 -TrustRepository; \
    Install-PSResource -Name Pester -Version 5.6.1 -TrustRepository"

# NOTE: Get-WinEvent is Windows-only (it calls the Windows Event Log API) and is NOT available
# in this Linux pwsh container. The lab therefore ships a pre-exported JSONL artifact
# (data/events.jsonl) produced by the cross-platform 'evtx' Rust CLI's evtx_dump, and Vigil
# consumes that. The gate needs no network and no evtx_dump. To re-export your own .evtx samples
# (e.g. from EVTX-ATTACK-SAMPLES) install the tool with `cargo install evtx` and run
# `evtx_dump -o jsonl sample.evtx` -- see this lab's cheatsheet.

COPY . /lab

CMD ["pwsh", "-NoLogo", "-Command", "Start-Sleep -Seconds 2147483647"]
