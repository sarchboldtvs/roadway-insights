#!/usr/bin/env python3
"""Fail on destructive changes in a Terraform or DCM plan.

  plan_lint.py terraform <plan.json>        (from `terraform show -json plan.out`)
  plan_lint.py dcm <plan output dir|file>   (from `snow dcm plan --save-output`)

Exit 1 on FAIL. Approval to proceed anyway is a person's decision recorded on
the issue (TF-05 / DEP-02); this script never accepts an override flag.
"""
import json
import pathlib
import re
import sys

PROTECTED_TF = ("snowflake_database", "snowflake_schema", "snowflake_account_role",
                "snowflake_role", "snowflake_warehouse", "snowflake_database_role")
DCM_DROP = re.compile(r"\b(DROP)\s+(DATABASE|SCHEMA|TABLE|STAGE|DYNAMIC TABLE)\b\s+([\w\".]+)", re.I)


def lint_tf(path):
    plan = json.loads(pathlib.Path(path).read_text())
    fails, warns = [], []
    for rc in plan.get("resource_changes", []):
        actions = rc.get("change", {}).get("actions", [])
        if "delete" in actions and rc.get("type", "").startswith(PROTECTED_TF):
            kind = "replace" if "create" in actions else "destroy"
            fails.append(f"{kind}: {rc['address']}")
        if rc.get("type") == "snowflake_database" and "create" in actions:
            warns.append(f"new database {rc['address']}: add lifecycle prevent_destroy (TF-04)")
    return fails, warns


def lint_dcm(path):
    p = pathlib.Path(path)
    files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
    fails = []
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for m in DCM_DROP.finditer(text):
            fails.append(f"DROP {m.group(2).upper()} {m.group(3)} ({f.name})")
        if f.suffix == ".json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            for line in json.dumps(data).split("{"):
                if re.search(r'"(operation|action)"\s*:\s*"drop"', line, re.I) and re.search(r"(database|schema|table|stage)", line, re.I):
                    fails.append(f"drop entry in {f.name}: {line[:120]}")
    return sorted(set(fails)), []


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("terraform", "dcm"):
        print(__doc__)
        return 2
    fails, warns = (lint_tf if sys.argv[1] == "terraform" else lint_dcm)(sys.argv[2])
    for w in warns:
        print(f"WARN  {w}")
    for f in fails:
        print(f"FAIL  {f}")
    print(f"plan_lint: {len(fails)} FAIL, {len(warns)} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
