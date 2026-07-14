# Vigil root module - dot-sources public functions and exports them explicitly.
# This is the same skeleton you built in Module 01; the capstone is where you integrate
# every phase's cmdlet into one shipped module.
$public = @(Get-ChildItem -Path "$PSScriptRoot/Public/*.ps1" -ErrorAction SilentlyContinue)
foreach ($file in $public) {
    . $file.FullName
}
Export-ModuleMember -Function $public.BaseName
