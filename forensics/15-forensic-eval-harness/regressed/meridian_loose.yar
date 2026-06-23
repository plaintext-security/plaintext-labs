/*
 * meridian_loose.yar — the REGRESSED dropper rule. This is the planted regression
 * the gate must catch: a well-meaning edit "to catch more variants" that quietly
 * loosens the rule until precision collapses.
 *
 * The change: instead of requiring the C2 domain OR the svchost32+/update.bin pair,
 * it now fires on "/update.bin" alone. That string also appears in the BENIGN
 * auto-updater fixture (pe-006-autoupdate.exe) — so the rule now flags benign
 * software. Recall is unchanged; PRECISION drops, and the precision-floor gate goes RED.
 *
 * Open this next to data/meridian.yar to see exactly which condition was weakened.
 */

rule MeridianDropper_Loose {
    meta:
        author      = "Plaintext Forensics"
        description = "REGRESSED — fires on /update.bin alone (too broad)"
    strings:
        $beacon = "/update.bin" ascii wide
    condition:
        uint16(0) == 0x5A4D and $beacon
}
