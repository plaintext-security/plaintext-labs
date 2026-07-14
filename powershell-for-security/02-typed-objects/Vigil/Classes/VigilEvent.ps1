# The VigilEvent type - Vigil's typed telemetry contract.
#
# Defined as a class (not a [pscustomobject]) because the type IDENTITY is load-bearing:
# ConvertTo-VigilEvent declares [OutputType([VigilEvent])], Module 03's parser and Module 04's
# enrichment bind to it, and downstream code can check `$e -is [VigilEvent]`. It is loaded via the
# manifest's ScriptsToProcess so [VigilEvent] resolves in the caller's session, not just inside the module.

class VigilEvent {
    [datetime]$TimeCreated
    [int]     $Id
    [string]  $Provider
    [string]  $Level
    [bool]    $Suspicious
    [string]  $Message

    VigilEvent(
        [datetime]$timeCreated,
        [int]$id,
        [string]$provider,
        [string]$level,
        [bool]$suspicious,
        [string]$message
    ) {
        $this.TimeCreated = $timeCreated
        $this.Id          = $id
        $this.Provider    = $provider
        $this.Level       = $level
        $this.Suspicious  = $suspicious
        $this.Message     = $message
    }
}
