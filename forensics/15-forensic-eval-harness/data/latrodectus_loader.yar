/*
 * latrodectus_loader.yar — the GOOD Module-12 dropper rule, scored here on a held-out corpus.
 *
 * Keys on the two indicators that are SPECIFIC to the Latrodectus loader (the
 * "Lunar Spider" anchor case):
 *   - the C2 domain "workspacin.cloud"
 *   - the masquerade name "svchost32" paired with the "/update.bin" beacon path
 * Precise on purpose: it does NOT fire on a legit auto-updater that merely ships an
 * "/update.bin", because that benign near-miss lacks the C2 domain and the masquerade name.
 *
 * ATT&CK: T1071.001 (Web Protocols), T1036.004 (Masquerade Task or Service).
 */

rule latrodectus_loader_c2_domain {
    meta:
        author      = "Plaintext Forensics"
        description = "Latrodectus loader — embedded C2 domain"
        reference   = "https://attack.mitre.org/techniques/T1071/001/"
    strings:
        $c2_domain = "workspacin.cloud" ascii wide
    condition:
        uint16(0) == 0x5A4D and $c2_domain
}

rule latrodectus_loader_network_persistence {
    meta:
        author      = "Plaintext Forensics"
        description = "Latrodectus loader — svchost32 masquerade + beacon path"
        reference   = "https://attack.mitre.org/techniques/T1036/004/"
    strings:
        $svchost_fake = "svchost32" ascii wide nocase
        $c2_path      = "/update.bin" ascii wide
    condition:
        uint16(0) == 0x5A4D and $svchost_fake and $c2_path
}
