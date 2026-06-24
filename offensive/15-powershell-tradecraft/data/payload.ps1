# Benign stand-in for a staged second-stage payload. In a real intrusion this would
# be the implant; here it just proves the cradle executed it *in memory* (nothing
# touched disk on the victim). The marker is what the demo greps for.
Write-Output "[payload] CORP-STAGE2 ran in memory on $(hostname) — no file written to disk"
