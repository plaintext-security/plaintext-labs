# Vigil root module - loads the VigilEvent type, dot-sources public functions, exports them explicitly.

# The class is also loaded via the manifest's ScriptsToProcess (for the caller's session); dot-source it
# here too so the module's own functions can reference [VigilEvent] at load time.
. "$PSScriptRoot/Classes/VigilEvent.ps1"

$public = @(Get-ChildItem -Path "$PSScriptRoot/Public/*.ps1" -ErrorAction SilentlyContinue)
foreach ($file in $public) {
    . $file.FullName
}
Export-ModuleMember -Function $public.BaseName
