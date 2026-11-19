#!/usr/bin/env python3
"""AI-DLC guard hook for GitHub Copilot (preToolUse).

Reads the hook payload (JSON) on stdin. If the call is a shell command that
matches a blocked pattern, prints one deny decision on stdout. Otherwise
prints nothing (Copilot's default behaviour applies).

Used three ways:
  repo hook    .github/hooks/aidlc-guard.json   -> python .aidlc/scripts/aidlc_guard.py
  policy hook  C:\\ProgramData\\GitHub\\Copilot\\policy.d\\aidlc-guard.json (Intune)
  self-test    python aidlc_guard.py --self-test

VERIFY in Pilot 0: payload field names (toolName / toolArgs) and the shell
tool name in the Copilot App. The script scans the whole payload of shell-like
tools, so it works whatever the exact argument field is called.
"""
import json
import re
import sys

ALLOWED_CONNECTIONS = {"aidlc_dev_ro", "aidlc_prod_ro", "aidlc_dev_rw"}

# (pattern, reason). Patterns are matched case-insensitively against the command text.
BLOCKED = [
    (r"\bterraform\b[^\n]*\b(apply|destroy|import)\b", "Terraform apply/destroy/import run only in CI (tf-apply / release workflows)."),
    (r"\btofu\b[^\n]*\b(apply|destroy|import)\b", "Infrastructure applies run only in CI."),
    (r"\bsnow\b[^\n]*\bdcm\b[^\n]*\bdeploy\b[^\n]*--target[ =]+\"?prod", "DCM PROD deploys run only in the release workflow."),
    (r"\bgh\b[^\n]*\b(issue|pr)\b[^\n]*\bedit\b[^\n]*--(add|remove)-label[^\n]*(phase:|plan-approved|accepted|dev-verified)", "Board-managed and gate labels are set by people and Board sync, never by an agent."),
    (r"\bgh\b[^\n]*\blabel\b[^\n]*\b(create|edit|delete|clone)\b", "Repository labels are managed by people."),
    (r"\bgh\b[^\n]*\bproject\b[^\n]*\bitem-(edit|archive|delete)\b", "Agents never move cards on the board."),
    (r"\bgh\b[^\n]*\bpr\b[^\n]*\bmerge\b", "Only a person merges pull requests."),
    (r"\bgh\b[^\n]*\bworkflow\b[^\n]*\brun\b[^\n]*\b(release|tf-apply)\b", "Release and Terraform apply workflows are started by people."),
    (r"\bgit\b[^\n]*\bpush\b[^\n]*(--force\b|-f\b|\bmain\b|\bmaster\b)", "No force pushes and no pushes to main."),
    (r"--dangerously-allow-all-tool-calls", "Cortex Code must run with permission prompts."),
    (r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r", "Recursive force deletes are blocked."),
    (r"\bremove-item\b[^\n]*-recurse[^\n]*-force", "Recursive force deletes are blocked."),
]

CONN_RE = re.compile(r"(?:--connection|(?<![\w-])-c)[ =]+\"?([A-Za-z0-9_\-]+)", re.I)
SHELLISH = re.compile(r"bash|shell|powershell|pwsh|terminal|exec|command|run", re.I)


def decide(payload: dict):
    tool = str(payload.get("toolName") or payload.get("tool_name") or payload.get("tool") or "")
    if tool and not SHELLISH.search(tool):
        return None
    text = json.dumps(payload.get("toolArgs", payload.get("tool_input", payload)))
    text = text.replace("\\n", "\n")
    for pattern, reason in BLOCKED:
        if re.search(pattern, text, re.I):
            return reason
    if re.search(r"\b(cortex|snow)\b", text, re.I):
        for conn in CONN_RE.findall(text):
            if conn.lower() not in ALLOWED_CONNECTIONS:
                return f"Snowflake connection '{conn}' is not an AI-DLC connection ({', '.join(sorted(ALLOWED_CONNECTIONS))})."
    return None


def self_test() -> int:
    cases = [
        ({"toolName": "bash", "toolArgs": {"command": "terraform -chdir=terraform apply"}}, True),
        ({"toolName": "bash", "toolArgs": {"command": "terraform -chdir=terraform plan"}}, False),
        ({"toolName": "powershell", "toolArgs": {"command": "gh issue edit 12 --add-label dev-verified"}}, True),
        ({"toolName": "bash", "toolArgs": {"command": "gh issue edit 12 --add-label priority:must"}}, False),
        ({"toolName": "bash", "toolArgs": {"command": "snow dcm deploy --target PROD --connection aidlc_dev_rw"}}, True),
        ({"toolName": "bash", "toolArgs": {"command": "snow dcm deploy --target DEV --connection aidlc_dev_rw"}}, False),
        ({"toolName": "bash", "toolArgs": {"command": "cortex -c accountadmin_conn -p 'hi'"}}, True),
        ({"toolName": "bash", "toolArgs": {"command": "git push origin main"}}, True),
        ({"toolName": "bash", "toolArgs": {"command": "git push origin 12-road-issues"}}, False),
        ({"toolName": "edit", "toolArgs": {"content": "run terraform apply in CI"}}, False),
    ]
    failed = 0
    for payload, should_block in cases:
        blocked = decide(payload) is not None
        if blocked != should_block:
            failed += 1
            print(f"FAIL: {payload} -> blocked={blocked}, expected {should_block}")
    print("self-test passed" if not failed else f"self-test FAILED ({failed})")
    return 1 if failed else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    reason = decide(payload)
    if reason:
        print(json.dumps({"permissionDecision": "deny",
                          "permissionDecisionReason": "AI-DLC guard: " + reason + " Ask a person (see AGENTS.md)."}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
