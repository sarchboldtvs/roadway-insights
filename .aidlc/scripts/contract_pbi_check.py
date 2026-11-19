#!/usr/bin/env python3
"""Check a Power BI semantic model (PBIP / TMDL) against an ODCS contract.

  contract_pbi_check.py <Name.SemanticModel dir> <contract.odcs.yaml>

CON-01 every Snowflake source object referenced in partitions is in the contract
CON-02 every source column used by the model exists in the contract
CON-03 column display names match the contract businessName (WARN)

Parsing is deliberately simple (regex over TMDL). VERIFY against the first
real model from powerbi-authoring and adjust. Requires PyYAML.
"""
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    print("contract_pbi_check: pip install pyyaml"); sys.exit(2)


def load_contract(path):
    c = yaml.safe_load(pathlib.Path(path).read_text())
    objects = {}
    for obj in c.get("schema", []):
        phys = (obj.get("physicalName") or obj.get("name", "")).upper()
        cols = {}
        for p in obj.get("properties", []) or []:
            cols[(p.get("physicalName") or p.get("name", "")).upper()] = p.get("businessName")
        objects[phys] = cols
    return objects


def main():
    if len(sys.argv) != 3:
        print(__doc__); return 2
    model_dir, contract = pathlib.Path(sys.argv[1]), sys.argv[2]
    objects = load_contract(contract)
    fails = warns = 0
    tmdl_files = list(model_dir.rglob("*.tmdl"))
    if not tmdl_files:
        print(f"FAIL  CON-00  no .tmdl files under {model_dir} (is the model saved as PBIP/TMDL?)"); return 1
    for f in tmdl_files:
        text = f.read_text(errors="ignore")
        sources = set(m.upper() for m in re.findall(r'(?:Item\s*=\s*"|\[Name\s*=\s*")([A-Za-z0-9_]+)"', text))
        for src in sources:
            if src in objects:
                continue
            if src.isupper() or src.startswith(("FCT_", "DIM_")):
                print(f"FAIL  CON-01  {f.name}: source {src} not in contract"); fails += 1
        matched = [s for s in sources if s in objects]
        if not matched:
            continue
        cols = objects[matched[0]]
        for m in re.finditer(r"^\s*column\s+'?([^'\n=]+?)'?\s*$((?:\n\s{2,}.*)*)", text, re.M):
            display, body = m.group(1).strip(), m.group(2)
            sc = re.search(r"sourceColumn:\s*([^\s]+)", body)
            if not sc:
                continue
            source_col = sc.group(1).strip('"').upper()
            if source_col not in cols:
                print(f"FAIL  CON-02  {f.name}: column {source_col} not in contract object {matched[0]}"); fails += 1
            elif cols[source_col] and cols[source_col] != display:
                print(f"WARN  CON-03  {f.name}: '{display}' should be '{cols[source_col]}' (businessName)"); warns += 1
    print(f"contract_pbi_check: {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
