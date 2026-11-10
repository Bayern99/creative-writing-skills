#!/usr/bin/env python3
"""
git_guard.py - PreToolUse hook for intercepting destructive git commands in Antigravity.
Prompts author confirmation (decision: ask) for git reset --hard, clean, restore, checkout --, revert.
"""

import sys
import json
import re

GIT_FLAG = r'(?:\s+-[^\s]+|\s+--[^\s]+|\s+(?!--)[^\s]+)*?'

DESTRUCTIVE_PATTERNS = [
    re.compile(r'\bgit\b' + GIT_FLAG + r'\s+reset(\s+\S+)*?\s+--hard(=|\b)', re.IGNORECASE),
    re.compile(r'\bgit\b' + GIT_FLAG + r'\s+clean\b', re.IGNORECASE),
    re.compile(r'\bgit\b' + GIT_FLAG + r'\s+restore\b', re.IGNORECASE),
    re.compile(r'\bgit\b' + GIT_FLAG + r'\s+checkout\s+(.*\s+)?--(\s+|$)', re.IGNORECASE),
    re.compile(r'\bgit\b' + GIT_FLAG + r'\s+revert\b', re.IGNORECASE),
]


def check_command(cmd: str) -> dict:
    for pattern in DESTRUCTIVE_PATTERNS:
        match = pattern.search(cmd)
        if match:
            matched_str = match.group(0).strip()
            return {
                "decision": "ask",
                "reason": (
                    f"Destructive git operation detected: '{matched_str}'. "
                    "Confirmation required to prevent unintentional story prose or repository loss."
                )
            }
    return {"decision": "allow"}


def main():
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        if not isinstance(payload, dict):
            print(json.dumps({"decision": "allow"}))
            return

        tool_call = payload.get("toolCall")
        if not isinstance(tool_call, dict):
            tool_call = {}

        args = tool_call.get("args")
        if not isinstance(args, dict):
            args = {}

        command_line = (
            args.get("CommandLine")
            or args.get("commandLine")
            or args.get("command")
            or args.get("cmd")
            or payload.get("CommandLine")
            or payload.get("commandLine")
            or payload.get("command")
            or ""
        )

        result = check_command(str(command_line))
        print(json.dumps(result))
    except Exception:
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
