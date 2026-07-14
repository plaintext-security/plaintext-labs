@{
    # Gate on Error and Warning. Suppress at the source WITH a justification, never by disabling rules here.
    Severity = @('Error', 'Warning')
    # The loose legacy/hunt.ps1 is intentionally dirty (it's what you migrate) — exclude it from the gate.
    ExcludeRules = @()
}
