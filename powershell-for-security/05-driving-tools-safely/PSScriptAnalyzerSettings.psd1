@{
    # Gate on Error and Warning. Suppress at the source WITH a justification, never by disabling rules
    # here. PSAvoidUsingInvokeExpression is the load-bearing rule for this module - it must stay ON.
    Severity = @('Error', 'Warning')
    ExcludeRules = @()
}
