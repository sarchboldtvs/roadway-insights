#!/usr/bin/env python3
"""Hub/solution PR gate for breaking contract changes.

  contract_gate.py <changelog output file> <contract.odcs.yaml> <pr number>

If the changelog marks a breaking change, every consumer team listed in the
contract's `consumers` custom property must have at least one member who
APPROVED the PR. Uses the gh CLI (GH_TOKEN needs read:org). Exit 1 if not met.
VERIFY the changelog output format of the installed Data Contract CLI.
"""
import json
import pathlib
import re
import subprocess
import sys

import yaml


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main():
    changelog, contract, pr = sys.argv[1], sys.argv[2], sys.argv[3]
    text = pathlib.Path(changelog).read_text(errors="ignore")
    if not re.search(r"\bbreaking\b", text, re.I) or re.search(r"\b0 breaking\b", text, re.I):
        print("contract_gate: no breaking change"); return 0
    c = yaml.safe_load(pathlib.Path(contract).read_text())
    consumers = []
    for prop in c.get("customProperties", []) or []:
        if prop.get("property") == "consumers":
            consumers = prop.get("value") or []
    teams = sorted({x.get("team") for x in consumers if x.get("team")})
    if not teams:
        print("::error::Breaking contract change but no consumer teams listed"); return 1
    repo = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                          capture_output=True, text=True).stdout.strip()
    reviews = json.loads(gh("api", f"repos/{repo}/pulls/{pr}/reviews", "--paginate"))
    approvers = {r["user"]["login"] for r in reviews if r.get("state") == "APPROVED"}
    missing = []
    for team in teams:
        org, slug = team.split("/", 1)
        ok = False
        for user in approvers:
            res = subprocess.run(["gh", "api", f"orgs/{org}/teams/{slug}/memberships/{user}"],
                                 capture_output=True, text=True)
            if res.returncode == 0 and '"active"' in res.stdout:
                ok = True; break
        if not ok:
            missing.append(team)
    if missing:
        print(f"::error::Breaking contract change needs approval from: {', '.join(missing)}"); return 1
    print("contract_gate: all consumer teams approved"); return 0


if __name__ == "__main__":
    sys.exit(main())
