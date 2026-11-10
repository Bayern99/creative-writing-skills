#!/usr/bin/env python3
"""Antigravity 2.0 Plugin Integrity Checker.

Strict referential integrity, schema compliance, and artifact validator
for creative-writing-skills Google Antigravity 2.0 native plugin.

Checks:
1. Manifest Integrity (plugin.json RFC 8259, kebab-case, semver, bounds)
2. Agent Topology & Model Policy (15 agents, muse: inherit, 14 subagents: flash,
   sandbox policy, mainAgent/subagent flags, role prompt constraints)
3. Skill Completeness (28 skills, SKILL.md names match folders, descriptions,
   body size <= 24,000 bytes, zero dangling resource links, key resources)
4. Rules Conformance (story-project.md: model_decision, kb-pages.md: glob, body <= 24KB)
5. Hooks & Safety Guards (hooks.json structure, git_guard.py executable chmod 0755)
6. Zero Claude / Mars Remnants (creative-writing-skills:, AskUserQuestion, NotebookEdit,
   Bash(, disallowedTools, meridian spawn, .mars/, opus, sonnet, argon, luna)
7. Strict CLI Validation (agy plugin validate --strict if agy is available)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PLUGIN_DIR = REPO_ROOT / "plugin" / "antigravity"
CONFIG_AGENTS_TOML = REPO_ROOT / "antigravity" / "agents.toml"

EXPECTED_AGENTS = [
    "muse",
    "writer",
    "character-sim",
    "outliner",
    "critic",
    "brainstormer",
    "continuity-checker",
    "reader-sim",
    "style-creator",
    "creative-researcher",
    "kb-lead",
    "explorer",
    "session-miner",
    "cold-reader",
    "kb-maintainer",
]

ENTRY_AGENTS = {"muse", "writer", "character-sim", "outliner"}
SUBAGENT_ONLY = {
    "critic",
    "brainstormer",
    "continuity-checker",
    "reader-sim",
    "style-creator",
    "creative-researcher",
    "kb-lead",
    "explorer",
    "session-miner",
    "cold-reader",
    "kb-maintainer",
}

REVIEWER_AGENTS = {
    "critic",
    "reader-sim",
    "continuity-checker",
    "cold-reader",
    "explorer",
    "session-miner",
}

EXPECTED_SKILLS = [
    "character-sim",
    "correct",
    "creative-research",
    "creative-writing-craft",
    "creative-writing-muse",
    "grill",
    "grill-with-docs",
    "information-hierarchy",
    "intent-modeling",
    "knowledge-layers",
    "llm-writing",
    "md-validation",
    "project-setup",
    "qi-layer",
    "qi-maintenance",
    "reader-sim",
    "reflect",
    "shared-dao",
    "shared-workspace",
    "story-memory",
    "story-planning",
    "story-review",
    "story-workflow",
    "structured-artifact",
    "writing-principles",
    "writing-staffing",
    "writing-sync",
    "zoom-out",
]

FORBIDDEN_REMNANTS = [
    (re.compile(r"creative-writing-skills:"), "creative-writing-skills:"),
    (re.compile(r"\bAskUserQuestion\b"), "AskUserQuestion"),
    (re.compile(r"\bNotebookEdit\b"), "NotebookEdit"),
    (re.compile(r"\bBash\("), "Bash("),
    (re.compile(r"\bdisallowedTools:"), "disallowedTools:"),
    (re.compile(r"\bmeridian\s+spawn\b"), "meridian spawn"),
    (re.compile(r"\.mars/"), ".mars/"),
    (re.compile(r"\bopus\b", re.IGNORECASE), "opus"),
    (re.compile(r"\bsonnet\b", re.IGNORECASE), "sonnet"),
    (re.compile(r"\bargon\b", re.IGNORECASE), "argon"),
    (re.compile(r"\bluna\b", re.IGNORECASE), "luna"),
]


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter and return (frontmatter_dict, body_text)."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    yaml_text = parts[1]
    body = parts[2]

    metadata: Dict[str, Any] = {}
    current_key: Optional[str] = None

    for raw_line in yaml_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("- ") and current_key:
            val = line[2:].strip().strip("\"'")
            if current_key not in metadata or not isinstance(metadata[current_key], list):
                metadata[current_key] = []
            metadata[current_key].append(val)
            continue

        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()

            if val == "":
                current_key = key
                metadata[key] = []
            elif val.lower() == "true":
                metadata[key] = True
                current_key = key
            elif val.lower() == "false":
                metadata[key] = False
                current_key = key
            elif val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                metadata[key] = items
                current_key = key
            elif (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                metadata[key] = val[1:-1]
                current_key = key
            elif val.isdigit():
                metadata[key] = int(val)
                current_key = key
            else:
                metadata[key] = val
                current_key = key

    return metadata, body


class Checker:
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def check_manifest(self) -> None:
        manifest_path = self.plugin_dir / "plugin.json"
        if not manifest_path.is_file():
            self.error("plugin.json manifest is missing")
            return

        raw_text = manifest_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            self.error(f"plugin.json is not valid strict JSON: {exc}")
            return

        # Core identity
        if data.get("name") != "creative-writing-skills":
            self.error(f"plugin.json name expected 'creative-writing-skills', got '{data.get('name')}'")
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", data.get("name", "")):
            self.error("plugin.json name is not strict kebab-case")

        version = data.get("version", "")
        if not re.match(r"^\d+\.\d+\.\d+", version):
            self.error(f"plugin.json version '{version}' does not match semver")

        # Logo
        logo = data.get("logo")
        if not logo or logo.startswith("/") or logo.startswith("http"):
            self.error(f"plugin.json logo must be a local relative path, got: {logo}")
        elif not (self.plugin_dir / logo).is_file():
            self.error(f"plugin.json logo file '{logo}' does not exist")

        # Suggested prompts
        prompts = data.get("suggestedPrompts", [])
        if not isinstance(prompts, list) or not (1 <= len(prompts) <= 3):
            self.error(f"suggestedPrompts must be an array of 1 to 3 items, got: {len(prompts)}")

        # URLs
        for field in ("homepage", "repository"):
            url = data.get(field)
            if url and not url.startswith("https://"):
                self.error(f"plugin.json {field} '{url}' must use HTTPS")

        # Disallowed top-level keys
        allowed_keys = {
            "$schema",
            "name",
            "version",
            "displayName",
            "description",
            "author",
            "homepage",
            "repository",
            "license",
            "logo",
            "keywords",
            "suggestedPrompts",
            "disabled",
        }
        unknown = set(data.keys()) - allowed_keys
        if unknown:
            self.error(f"plugin.json contains disallowed fields: {unknown}")

    def check_agents(self) -> None:
        agents_dir = self.plugin_dir / "agents"
        if not agents_dir.is_dir():
            self.error("agents/ directory is missing")
            return

        found_agents = sorted([p.stem for p in agents_dir.glob("*.md")])
        if found_agents != sorted(EXPECTED_AGENTS):
            missing = set(EXPECTED_AGENTS) - set(found_agents)
            extra = set(found_agents) - set(EXPECTED_AGENTS)
            self.error(f"Agent roster mismatch. Missing: {missing}, Extra: {extra}")

        for agent_file in agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            content = agent_file.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)

            # Frontmatter name & description
            if fm.get("name") != agent_name:
                self.error(f"Agent {agent_name}: frontmatter name '{fm.get('name')}' != '{agent_name}'")
            if not fm.get("description"):
                self.error(f"Agent {agent_name}: missing or empty description")

            # Model policy: muse = inherit, 14 subagents = flash
            model = fm.get("model")
            if agent_name == "muse":
                if model != "inherit":
                    self.error(f"Agent muse: model must be 'inherit', got '{model}'")
            else:
                if model != "flash":
                    self.error(f"Subagent {agent_name}: model must be 'flash', got '{model}'")

            # Execution policy
            policy = fm.get("commandExecutionPolicy")
            if policy not in {"sandbox", "auto"}:
                self.error(f"Agent {agent_name}: invalid commandExecutionPolicy '{policy}' (must be sandbox/auto)")

            # Flags
            expected_main = agent_name in ENTRY_AGENTS
            if (fm.get("mainAgent") is True) != expected_main:
                self.error(f"Agent {agent_name}: mainAgent expected {expected_main}, got {fm.get('mainAgent')}")

            expected_subagent = agent_name != "muse"
            if (fm.get("subagent") is True) != expected_subagent:
                self.error(f"Agent {agent_name}: subagent expected {expected_subagent}, got {fm.get('subagent')}")

            # Forbidden fields
            for forbidden in ("disallowedTools", "effort", "tools"):
                if forbidden in fm:
                    self.error(f"Agent {agent_name}: contains forbidden frontmatter key '{forbidden}'")

            # Prompt body checks
            body_bytes = len(body.strip().encode("utf-8"))
            if body_bytes < 100:
                self.error(f"Agent {agent_name}: body too short ({body_bytes} bytes)")

            body_lower = body.lower()
            if agent_name in REVIEWER_AGENTS:
                read_only_terms = ("read-only", "writes no files", "do not edit", "write no files", "does not edit", "edits nothing")
                if not any(t in body_lower for t in read_only_terms):
                    self.error(f"Reviewer agent {agent_name}: lacks explicit read-only prompt constraint")

            if agent_name in SUBAGENT_ONLY:
                caller_terms = ("caller", "do not prompt", "never prompt", "return", "report")
                if not any(t in body_lower for t in caller_terms):
                    self.error(f"Subagent {agent_name}: lacks caller-reporting prompt constraint")

            # Check skill references in frontmatter
            for skill_ref in fm.get("skills", []) + fm.get("optional_skills", []):
                skill_dir_name = skill_ref.replace("skills/", "")
                if not (self.plugin_dir / "skills" / skill_dir_name).is_dir():
                    self.error(f"Agent {agent_name}: references non-existent skill '{skill_ref}'")

    def check_skills(self) -> None:
        skills_dir = self.plugin_dir / "skills"
        if not skills_dir.is_dir():
            self.error("skills/ directory is missing")
            return

        found_skills = sorted([p.name for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")])
        if found_skills != sorted(EXPECTED_SKILLS):
            missing = set(EXPECTED_SKILLS) - set(found_skills)
            extra = set(found_skills) - set(EXPECTED_SKILLS)
            self.error(f"Skill inventory mismatch. Missing: {missing}, Extra: {extra}")

        link_regex = re.compile(r"\[.*?\]\((resources/[^#\)]+)(?:#[^\)]*)?\)")

        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir() or skill_path.name.startswith("."):
                continue

            skill_name = skill_path.name
            skill_md = skill_path / "SKILL.md"
            if not skill_md.is_file():
                self.error(f"Skill {skill_name}: missing SKILL.md")
                continue

            content = skill_md.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)

            if fm.get("name") != skill_name:
                self.error(f"Skill {skill_name}: frontmatter name '{fm.get('name')}' != folder '{skill_name}'")
            if not fm.get("description"):
                self.error(f"Skill {skill_name}: missing or empty description")

            body_bytes = len(body.encode("utf-8"))
            if body_bytes > 24000:
                self.error(f"Skill {skill_name}: body is {body_bytes} bytes, exceeds 24,000 byte limit")

            # Check markdown links
            for match in link_regex.finditer(content):
                rel_target = match.group(1)
                target_file = skill_path / rel_target
                if not target_file.exists():
                    self.error(f"Skill {skill_name}: dangling resource link '{rel_target}'")

        # Key resources verification
        key_resources = [
            skills_dir / "creative-writing-craft" / "resources" / "prose-modes.md",
            skills_dir / "writing-principles" / "resources" / "antipatterns.md",
            skills_dir / "story-planning" / "resources" / "story-architecture.md",
            skills_dir / "project-setup" / "resources" / "antigravity.md",
            skills_dir / "writing-staffing" / "resources" / "antigravity-dispatch.md",
        ]
        for kr in key_resources:
            if not kr.is_file():
                self.error(f"Key skill resource missing: {kr.relative_to(self.plugin_dir)}")

    def check_rules(self) -> None:
        rules_dir = self.plugin_dir / "rules"
        if not rules_dir.is_dir():
            self.error("rules/ directory is missing")
            return

        story_rule = rules_dir / "story-project.md"
        if not story_rule.is_file():
            self.error("rules/story-project.md is missing")
        else:
            fm, body = parse_frontmatter(story_rule.read_text(encoding="utf-8"))
            if fm.get("trigger") != "model_decision":
                self.error(f"story-project.md trigger must be 'model_decision', got '{fm.get('trigger')}'")
            if not fm.get("description"):
                self.error("story-project.md missing description")
            if len(body.encode("utf-8")) > 24000:
                self.error("story-project.md exceeds 24,000 bytes")

        kb_rule = rules_dir / "kb-pages.md"
        if not kb_rule.is_file():
            self.error("rules/kb-pages.md is missing")
        else:
            fm, body = parse_frontmatter(kb_rule.read_text(encoding="utf-8"))
            if fm.get("trigger") != "glob":
                self.error(f"kb-pages.md trigger must be 'glob', got '{fm.get('trigger')}'")
            if not fm.get("globs"):
                self.error("kb-pages.md missing globs")
            if len(body.encode("utf-8")) > 24000:
                self.error("kb-pages.md exceeds 24,000 bytes")

    def check_hooks(self) -> None:
        hooks_json = self.plugin_dir / "hooks.json"
        if not hooks_json.is_file():
            self.error("hooks.json is missing")
            return

        try:
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.error(f"hooks.json is not valid JSON: {exc}")
            return

        # Check grouped PreToolUse hook
        guard_hook = data.get("git-guard", {})
        pre_tool_use = guard_hook.get("PreToolUse", [])
        if not isinstance(pre_tool_use, list) or not pre_tool_use:
            self.error("hooks.json missing PreToolUse grouped hook list")
            return

        entry = pre_tool_use[0]
        hooks_list = entry.get("hooks", [])
        if not hooks_list:
            self.error("PreToolUse entry missing 'hooks' handler list")
            return

        cmd = hooks_list[0].get("command", "")
        # Command should point to ./scripts/git_guard.py
        script_rel = cmd.lstrip("./")
        script_file = self.plugin_dir / script_rel
        if not script_file.is_file():
            self.error(f"Hook command script does not exist: {script_file}")
        elif not os.access(script_file, os.X_OK):
            self.error(f"Hook command script is not executable: {script_file}")

    def check_remnants(self) -> None:
        for root, _, files in os.walk(self.plugin_dir):
            for file in files:
                if not file.endswith((".md", ".json", ".py", ".yaml", ".yml", ".tmpl")):
                    continue
                path = Path(root) / file
                text = path.read_text(encoding="utf-8", errors="ignore")

                for pattern, label in FORBIDDEN_REMNANTS:
                    match = pattern.search(text)
                    if match:
                        rel = path.relative_to(self.plugin_dir)
                        # Find line number
                        line_no = text[: match.start()].count("\n") + 1
                        snippet = text[max(0, match.start() - 30) : min(len(text), match.end() + 30)].replace("\n", " ")
                        self.error(f"Forbidden remnant '{label}' found in {rel}:{line_no}: '...{snippet}...'")

    def check_agy_validate_strict(self) -> None:
        # Check if agy binary is available
        agy_cmd = shutil.which("agy") or "/home/antigravity/.local/bin/agy"
        if not os.path.exists(agy_cmd):
            self.warn("agy CLI not found on PATH; skipping agy plugin validate check")
            return

        cmd = [agy_cmd, "plugin", "validate", str(self.plugin_dir), "--strict", "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            self.error(f"`agy plugin validate --strict` failed (exit {proc.returncode}):\n{proc.stderr or proc.stdout}")
            return

        try:
            report = json.loads(proc.stdout)
            findings = report.get("findings", [])
            if findings:
                self.error(f"`agy plugin validate --strict` emitted findings: {findings}")
            components = report.get("components", {})
            if components.get("agents") != 15:
                self.error(f"`agy validate` discovered {components.get('agents')} agents, expected 15")
            if components.get("skills") != 28:
                self.error(f"`agy validate` discovered {components.get('skills')} skills, expected 28")
        except json.JSONDecodeError:
            self.error("Failed to parse JSON report from `agy plugin validate`")

    def run_all(self) -> bool:
        print(f"Running Antigravity 2.0 integrity checks on: {self.plugin_dir}")
        self.check_manifest()
        self.check_agents()
        self.check_skills()
        self.check_rules()
        self.check_hooks()
        self.check_remnants()
        self.check_agy_validate_strict()

        if self.warnings:
            for w in self.warnings:
                print(f"[WARN] {w}", file=sys.stderr)

        if self.errors:
            print(f"\nFAILED: {len(self.errors)} integrity error(s) discovered:", file=sys.stderr)
            for err in self.errors:
                print(f"  ❌ {err}", file=sys.stderr)
            return False

        print("\nALL INTEGRITY CHECKS PASSED: plugin/antigravity is clean, compliant, and verified.")
        return True


def main() -> None:
    plugin_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PLUGIN_DIR
    checker = Checker(plugin_dir)
    success = checker.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
