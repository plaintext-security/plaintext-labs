/*
 * Meridian Financial — deliberately vulnerable authentication stub.
 *
 * Compile with mitigations disabled (for teaching purposes only):
 *   gcc -O0 -fno-stack-protector -z execstack -no-pie -o meridian-login vuln.c
 *
 * Vulnerability: vuln() reads up to 256 bytes into a 64-byte stack buffer.
 * Stack layout at vuln() entry (with -O0 on x86-64):
 *
 *   ┌───────────────────────────────┐  ← rsp
 *   │  char buf[64]     (0x40 bytes) │
 *   ├───────────────────────────────┤  + 64
 *   │  ssize_t n        (8 bytes)   │  local variable
 *   ├───────────────────────────────┤  + 72
 *   │  saved rbp        (8 bytes)   │
 *   ├───────────────────────────────┤  + 80
 *   │  saved rip  ← OVERWRITE HERE  │
 *   └───────────────────────────────┘
 *
 * Offset to saved rip: 64 (buf) + 8 (n) + 8 (saved rbp) = 80 bytes.
 *
 * DO NOT use on production systems. Intentionally vulnerable for education.
 */
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/* Target function: demonstrates redirected execution. */
void win(void) {
    write(1, "[+] win() reached — saved RIP overwritten successfully\n", 56);
    write(1, "[+] In a real exploit this becomes a shell or stage-2 payload\n", 63);
    _exit(42);  /* exit code 42 = exploit success (detected by demo script) */
}

/* Vulnerable function: copies unbounded input into a fixed-size buffer. */
void vuln(void) {
    char buf[64];
    /* BUG: reads up to 256 bytes into a 64-byte buffer — no bounds check */
    ssize_t n = read(0, buf, 256);
    if (n > 0) {
        write(1, "Echo: ", 6);
        write(1, buf, n);
    }
}

int main(void) {
    write(1, "Meridian Financial — intranet token auth\n", 41);
    write(1, "Enter token: ", 13);
    vuln();
    write(1, "Auth complete.\n", 15);
    return 0;
}
