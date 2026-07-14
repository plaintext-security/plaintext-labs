# Vigil root module - dot-sources public functions and exports them explicitly.
$public = @(Get-ChildItem -Path "$PSScriptRoot/Public/*.ps1" -ErrorAction SilentlyContinue)
foreach ($file in $public) {
    . $file.FullName
}
Export-ModuleMember -Function $public.BaseName
