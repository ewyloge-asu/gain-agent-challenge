#!/usr/bin/env python3
"""
API-key onboarding helper (shared across the bundle).

Fixes the demo blocker: "it needs an API-key plug-in path anyone can use." It detects which
optional keys are present, tells the user exactly where to get each one (free), prompts for
any that are missing, and writes a gitignored credentials.env the skills auto-load.

Keys only UNLOCK richer tiers — they NEVER gate the core run. Every skill works offline at
Tier 0 using shipped snapshots, so a reviewer with no keys can still reproduce the findings.

Usage:
  python3 setup_keys.py            # interactive: fill in any missing keys
  python3 setup_keys.py --check    # just report what's set / missing (no prompts)

Standard library only.
"""
import argparse
import os
import sys

CRED_FILE = "credentials.env"

# Registry of optional keys the bundle can use. Add a row to support a new source.
KEYS = [
    {"env": "CONGRESS_GOV_API_KEY", "name": "Congress.gov",
     "signup": "https://api.congress.gov/sign-up/",
     "unlocks": "sponsored bills + policy areas (the 'act' leg of pay-the-gavel)"},
    {"env": "FEC_API_KEY", "name": "FEC (OpenFEC)",
     "signup": "https://api.open.fec.gov/developers/  (or any api.data.gov key)",
     "unlocks": "campaign-finance denominator (lobbyist $ as a share of receipts)"},
    {"env": "DATA_GOV_API_KEY", "name": "api.data.gov (data.gov catalog v4, regulations.gov)",
     "signup": "https://api.data.gov/signup/",
     "unlocks": "keyed dataset discovery + several federal APIs (one key works across many)"},
    {"env": "COURTLISTENER_API_TOKEN", "name": "CourtListener / RECAP",
     "signup": "https://www.courtlistener.com/help/api/rest/  (free account → API token)",
     "unlocks": "court dockets & filings for legal cross-checks"},
]


def read_existing() -> dict:
    vals = {}
    if os.path.exists(CRED_FILE):
        with open(CRED_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
    # env vars also count as "set"
    for k in list(k["env"] for k in KEYS):
        if os.environ.get(k):
            vals.setdefault(k, os.environ[k])
    return vals


def report(existing: dict) -> None:
    print("\nAPI key status (all optional — Tier 0 runs with none):\n")
    for k in KEYS:
        state = "SET  " if existing.get(k["env"]) else "unset"
        print(f"  [{state}] {k['env']}  — {k['name']}")
        print(f"           unlocks: {k['unlocks']}")
        if not existing.get(k["env"]):
            print(f"           get one: {k['signup']}")
    print()


def interactive(existing: dict) -> dict:
    vals = dict(existing)
    print("\nEnter any keys you have (Enter to skip; keys are optional).\n")
    for k in KEYS:
        if vals.get(k["env"]):
            print(f"  • {k['env']} already set — skipping.")
            continue
        print(f"  • {k['name']}  (get one free: {k['signup']})")
        try:
            v = input(f"    {k['env']} = ").strip()
        except EOFError:
            v = ""
        if v:
            vals[k["env"]] = v
    return vals


def write_creds(vals: dict) -> None:
    lines = ["# Bundle API keys — gitignored. All optional; Tier 0 needs none.",
             "# Regenerate/update with: python3 setup_keys.py", ""]
    for k in KEYS:
        v = vals.get(k["env"], "")
        lines.append(f"# {k['name']}: {k['signup']}")
        lines.append(f"{k['env']}={v}")
        lines.append("")
    with open(CRED_FILE, "w") as f:
        f.write("\n".join(lines))
    os.chmod(CRED_FILE, 0o600)


def main() -> int:
    p = argparse.ArgumentParser(description="Bundle API-key onboarding helper")
    p.add_argument("--check", action="store_true", help="report status only, no prompts")
    args = p.parse_args()

    existing = read_existing()
    report(existing)
    if args.check:
        return 0

    if not sys.stdin.isatty():
        print("(non-interactive shell; run without --check in a terminal to enter keys.)")
        return 0

    vals = interactive(existing)
    write_creds(vals)
    print(f"\n✓ wrote {CRED_FILE} (permissions 600). It is gitignored — never commit it.")
    print("  Skills load it automatically. Snapshots keep keyed findings re-runnable offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
