# Vigil root module - dot-sources private then public functions and exports only the public ones.
$private = @(Get-ChildItem -Path "$PSScriptRoot/Private/*.ps1" -ErrorAction SilentlyContinue)
$public = @(Get-ChildItem -Path "$PSScriptRoot/Public/*.ps1" -ErrorAction SilentlyContinue)
foreach ($file in @($private) + @($public)) {
    . $file.FullName
}
Export-ModuleMember -Function $public.BaseName
