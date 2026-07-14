# Vigil root module - dot-sources public functions and exports them explicitly.
# The JEA capability files live under ./jea and are data, not code - not dot-sourced here.
$public = @(Get-ChildItem -Path "$PSScriptRoot/Public/*.ps1" -ErrorAction SilentlyContinue)
foreach ($file in $public) {
    . $file.FullName
}
Export-ModuleMember -Function $public.BaseName
