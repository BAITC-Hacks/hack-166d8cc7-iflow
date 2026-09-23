"""Create private local access credentials; never print tokens or overwrite API keys."""
import argparse
import json
from pathlib import Path
import secrets
from dotenv import dotenv_values, set_key


def provision(path, employees, hr=False):
    values = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
    identities = json.loads(values.get("DEV_IDENTITIES_JSON") or "{}")
    identities = {k: v for k, v in identities.items() if k not in {"demo-hr", "demo-active", "demo-employee"}}
    requested = [{"role": "employee", "employee_id": employee} for employee in employees]
    if hr:
        requested.append({"role": "hr"})
    for principal in requested:
        if principal not in identities.values():
            identities[secrets.token_urlsafe(32)] = principal
    set_key(str(path), "DEV_IDENTITIES_JSON", json.dumps(identities), encoding="utf-8-sig")
    return len(identities)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--employee", action="append", default=[])
    parser.add_argument("--hr", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / ".env"
    count = provision(path, args.employee, args.hr)
    print(f"Configured {count} private identities in .env DEV_IDENTITIES_JSON. Restart backend. Tokens were not printed.")
