#!/usr/bin/env python3
"""
Reference port scanner and banner grabber.
Uses standard library only.

Target is the real Apache Solr 8.11.0 image (Vulhub Log4Shell / CVE-2021-44228
reference). Solr's HTTP/Jetty admin listens on 8983 (not 80), so an HTTP probe
is sent for 8983 as well; the banner grab is otherwise generic and works for any
service that replies on connect.
"""

import argparse
import socket

HTTP_PROBE = b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n"


def grab_banner(host: str, port: int, timeout: float = 1.0) -> str:
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            if port in (80, 8080, 8983):
                s.sendall(HTTP_PROBE)
            try:
                banner = s.recv(1024).decode("utf-8", errors="replace").strip()
                return banner[:120] if banner else "(no banner)"
            except OSError:
                return "(no banner)"
    except Exception:
        return "(error)"


def scan(host: str, ports: list[int], timeout: float = 1.0) -> None:
    print(f"{'PORT':<8} {'STATUS':<8} BANNER")
    print("-" * 60)
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            banner = grab_banner(host, port, timeout)
            print(f"{port:<8} {'OPEN':<8} {banner}")
        else:
            print(f"{port:<8} {'CLOSED':<8}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Port scanner and banner grabber.")
    parser.add_argument("--host", required=True)
    parser.add_argument("--ports", required=True, help="Comma-separated port list")
    parser.add_argument("--timeout", type=float, default=1.0)
    args = parser.parse_args()
    ports = [int(p.strip()) for p in args.ports.split(",")]
    scan(args.host, ports, args.timeout)


if __name__ == "__main__":
    main()
