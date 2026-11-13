#!/usr/bin/env python3
"""Deterministic Build Script for Google Antigravity 2.0 Native Plugin.

Zero-dependency Python 3.11 script converting the creative-writing-skills
Mars-resolved dependency closure in plugin/claude/ into a native Antigravity 2.0
plugin at plugin/antigravity/.

Pipeline:
1. Validates and copies package metadata from mars.toml into plugin.json
2. Transforms 15 agents from plugin/claude/agents/*.md using antigravity/agents.toml
   (applying role-specific inherit/flash models, sandbox policy, role constraints)
3. Copies and transforms all 27 skills from plugin/claude/skills/*
   (rewriting /creative-writing-skills:<skill> -> /<skill>, stripping Claude artifacts)
4. Applies antigravity/patches.toml with strict SHA-256 integrity verification
5. Injects antigravity/overlay/ assets, rules, guides, hooks.json, and git_guard.py
6. Sets executable permissions (chmod 0755) on scripts/git_guard.py
7. Guarantees deterministic, reproducible output
"""

import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCE_CLAUDE_DIR = REPO_ROOT / "plugin" / "claude"
CONFIG_AGENTS_TOML = REPO_ROOT / "antigravity" / "agents.toml"
CONFIG_PATCHES_TOML = REPO_ROOT / "antigravity" / "patches.toml"
OVERLAY_DIR = REPO_ROOT / "antigravity" / "overlay"
MARS_TOML = REPO_ROOT / "mars.toml"
ROOT_LICENSE = REPO_ROOT / "LICENSE"

DEFAULT_TARGET_DIR = REPO_ROOT / "plugin" / "antigravity"

REVIEWER_AGENTS = {
    "critic",
    "reader-sim",
    "continuity-checker",
    "cold-reader",
    "explorer",
    "session-miner",
}

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

ENTRY_AGENTS = {"muse", "writer", "character-sim", "outliner"}

SKILL_REF_PATTERN_SLASH = re.compile(r"/creative-writing-skills:([a-zA-Z0-9_-]+)")
SKILL_REF_PATTERN_PLAIN = re.compile(r"\bcreative-writing-skills:([a-zA-Z0-9_-]+)")

OBSOLETE_SETUP_RESOURCES = {
    "meridian-cli.md",
    "claude-code.md",
    "claude-desktop.md",
    "other-harnesses.md",
}


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter and return (frontmatter_dict, body_text)."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    yaml_text = parts[1]
    body = parts[2]

    # Clean line-by-line fallback parser for basic YAML
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


def rewrite_skill_references(text: str) -> str:
    """Rewrite Claude /creative-writing-skills:<skill> syntax to native /<skill>."""
    text = SKILL_REF_PATTERN_SLASH.sub(r"/\1", text)
    text = SKILL_REF_PATTERN_PLAIN.sub(r"\1", text)
    return text


def load_patches() -> Dict[str, Dict[str, Any]]:
    """Load antigravity/patches.toml into a lookup dictionary keyed by target file path."""
    if not CONFIG_PATCHES_TOML.is_file():
        raise FileNotFoundError(f"Missing patches configuration: {CONFIG_PATCHES_TOML}")

    with open(CONFIG_PATCHES_TOML, "rb") as fp:
        data = tomllib.load(fp)

    patches_by_file: Dict[str, Dict[str, Any]] = {}
    for patch in data.get("patches", []):
        patches_by_file[patch["file"]] = patch

    return patches_by_file


def apply_patch_if_present(
    rel_path: str,
    source_bytes: bytes,
    patches_by_file: Dict[str, Dict[str, Any]],
) -> str:
    """Verify SHA-256 and apply search/replace patch if declared for rel_path."""
    content = source_bytes.decode("utf-8")
    if rel_path in patches_by_file:
        patch = patches_by_file[rel_path]
        expected_sha = patch["sha256"]
        actual_sha = hashlib.sha256(source_bytes).hexdigest()
        if actual_sha != expected_sha:
            raise RuntimeError(
                f"SHA-256 verification failed for patch on '{rel_path}':\n"
                f"  Expected: {expected_sha}\n"
                f"  Actual:   {actual_sha}"
            )
        search_block = patch["search"]
        replace_block = patch["replace"]
        if search_block not in content:
            raise RuntimeError(
                f"Patch search block not found in '{rel_path}':\n{search_block[:100]}..."
            )
        content = content.replace(search_block, replace_block)
    return content


def build_manifest(target_dir: Path) -> None:
    """Generate RFC 8259 compliant plugin.json from overlay template and mars.toml."""
    tmpl_path = OVERLAY_DIR / "plugin.json.tmpl"
    if not tmpl_path.is_file():
        raise FileNotFoundError(f"Missing plugin manifest template: {tmpl_path}")

    with open(tmpl_path, "r", encoding="utf-8") as fp:
        manifest_data = json.load(fp)

    if MARS_TOML.is_file():
        with open(MARS_TOML, "rb") as fp:
            mars_data = tomllib.load(fp)
        pkg = mars_data.get("package", {})
        if "name" in pkg:
            manifest_data["name"] = pkg["name"]
        if "version" in pkg:
            manifest_data["version"] = pkg["version"]
        if "description" in pkg:
            # Keep clean one-line description
            desc = pkg["description"].strip().replace("\n", " ")
            manifest_data["description"] = desc
        if "license" in pkg:
            manifest_data["license"] = pkg["license"]
        manifest_data["homepage"] = "https://github.com/Bayern99/creative-writing-skills"
        manifest_data["repository"] = "https://github.com/Bayern99/creative-writing-skills"
        if "authors" in pkg and pkg["authors"]:
            author_str = pkg["authors"][0]
            m = re.match(r"^([^<]+)<([^>]+)>", author_str)
            if m:
                manifest_data["author"] = {
                    "name": m.group(1).strip(),
                    "email": m.group(2).strip(),
                }
            else:
                manifest_data["author"] = {"name": author_str.strip()}

    target_manifest = target_dir / "plugin.json"
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(target_manifest, "w", encoding="utf-8") as fp:
        json.dump(manifest_data, fp, indent=2, ensure_ascii=False)
        fp.write("\n")


def build_agents(
    target_dir: Path,
    patches_by_file: Dict[str, Dict[str, Any]],
) -> None:
    """Transform all 15 agents from plugin/claude/agents/ using antigravity/agents.toml."""
    if not CONFIG_AGENTS_TOML.is_file():
        raise FileNotFoundError(f"Missing agents configuration: {CONFIG_AGENTS_TOML}")

    with open(CONFIG_AGENTS_TOML, "rb") as fp:
        agents_toml = tomllib.load(fp)

    defaults = agents_toml.get("defaults", {})
    default_policy = defaults.get("commandExecutionPolicy", "sandbox")
    default_model = defaults.get("model", "flash")
    agents_table = agents_toml.get("agents", {})

    target_agents_dir = target_dir / "agents"
    target_agents_dir.mkdir(parents=True, exist_ok=True)

    source_agents_dir = SOURCE_CLAUDE_DIR / "agents"
    if not source_agents_dir.is_dir():
        raise FileNotFoundError(f"Source agents directory missing: {source_agents_dir}")

    for source_file in sorted(source_agents_dir.glob("*.md")):
        agent_name = source_file.stem
        raw_bytes = source_file.read_bytes()

        # Apply patch if declared (e.g. agents/session-miner.md)
        rel_agent_path = f"agents/{source_file.name}"
        patched_text = apply_patch_if_present(rel_agent_path, raw_bytes, patches_by_file)

        src_fm, raw_body = parse_frontmatter(patched_text)

        agent_cfg = agents_table.get(agent_name, {})

        # Muse follows the session selector; specialists use their configured tier.
        if agent_name == "muse":
            model = "inherit"
        else:
            model = agent_cfg.get("model", default_model)
            if model not in {"flash", "flash_lite", "pro", "inherit"}:
                model = "flash"

        main_agent = agent_cfg.get("mainAgent", agent_name in ENTRY_AGENTS)
        subagent = agent_cfg.get("subagent", agent_name != "muse")
        policy = agent_cfg.get("commandExecutionPolicy", default_policy)

        description = agent_cfg.get("description") or src_fm.get("description", "")
        # Escape double quotes for clean YAML string
        clean_desc = description.strip().replace('"', '\\"')

        skills_list = agent_cfg.get("skills", [])
        optional_skills_list = agent_cfg.get("optional_skills", [])
        subagents_list = agent_cfg.get("subagents", [])

        # Rewrite skill references in body
        body = rewrite_skill_references(raw_body.strip())

        # Append role constraints
        if agent_name in REVIEWER_AGENTS:
            body += (
                "\n\n## Role Constraints\n"
                "- **Read-only**: This agent is strictly read-only and writes no files.\n"
                "- **Reporting**: Do not prompt the user directly; return all findings, reports, and questions to the caller."
            )
        elif agent_name in SUBAGENT_ONLY:
            body += (
                "\n\n## Role Constraints\n"
                "- **Reporting**: Do not prompt the user directly; return all deliverables, open questions, and choices to the caller."
            )
        elif agent_name in ENTRY_AGENTS and agent_name != "muse":
            body += (
                "\n\n## Subagent Invocation Guidance\n"
                "When invoked as a subagent by an orchestrator, do not prompt the user directly; "
                "return all deliverables, open questions, and options to the calling agent."
            )

        # Build clean Antigravity frontmatter
        lines = [
            "---",
            f"name: {agent_name}",
            f'description: "{clean_desc}"',
            f"model: {model}",
            f"commandExecutionPolicy: {policy}",
            f"mainAgent: {'true' if main_agent else 'false'}",
            f"subagent: {'true' if subagent else 'false'}",
        ]

        tools_list = agent_cfg.get("tools", [])
        if tools_list:
            lines.append("tools:")
            for t in tools_list:
                lines.append(f"  - {t}")

        if skills_list:
            lines.append("skills:")
            for sk in skills_list:
                lines.append(f"  - {sk}")

        lines.append("---")
        lines.append("")
        lines.append(body)
        lines.append("")

        target_file = target_agents_dir / f"{agent_name}.md"
        target_file.write_text("\n".join(lines), encoding="utf-8")


def build_skills(
    target_dir: Path,
    patches_by_file: Dict[str, Dict[str, Any]],
) -> None:
    """Copy and transform all skills from the resolved plugin/claude/skills/ tree."""
    source_skills_dir = SOURCE_CLAUDE_DIR / "skills"
    if not source_skills_dir.is_dir():
        raise FileNotFoundError(f"Source skills directory missing: {source_skills_dir}")

    target_skills_dir = target_dir / "skills"
    target_skills_dir.mkdir(parents=True, exist_ok=True)

    text_extensions = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".toml"}

    for skill_path in sorted(source_skills_dir.iterdir()):
        if not skill_path.is_dir() or skill_path.name.startswith("."):
            continue

        skill_name = skill_path.name
        dest_skill_dir = target_skills_dir / skill_name
        dest_skill_dir.mkdir(parents=True, exist_ok=True)

        for src_item in sorted(skill_path.rglob("*")):
            if src_item.is_dir():
                continue
            if "__pycache__" in src_item.parts or any(p.startswith(".") for p in src_item.parts):
                continue

            rel_to_skill = src_item.relative_to(skill_path)

            # Skip obsolete non-Antigravity harness guides in project-setup
            if skill_name == "project-setup" and rel_to_skill.name in OBSOLETE_SETUP_RESOURCES:
                continue

            dest_item = dest_skill_dir / rel_to_skill
            dest_item.parent.mkdir(parents=True, exist_ok=True)

            rel_to_claude = f"skills/{skill_name}/{rel_to_skill.as_posix()}"
            raw_bytes = src_item.read_bytes()

            # Apply patch if present
            content_text = apply_patch_if_present(rel_to_claude, raw_bytes, patches_by_file)

            if src_item.suffix in text_extensions:
                content_text = rewrite_skill_references(content_text)
                dest_item.write_text(content_text, encoding="utf-8")
            else:
                dest_item.write_bytes(raw_bytes)


def copy_overlay_and_assets(target_dir: Path) -> None:
    """Copy overlay rules, assets, guides, README, hooks, and executable scripts."""
    if not OVERLAY_DIR.is_dir():
        raise FileNotFoundError(f"Overlay directory missing: {OVERLAY_DIR}")

    # Copy README.md
    overlay_readme = OVERLAY_DIR / "README.md"
    if overlay_readme.is_file():
        shutil.copy2(overlay_readme, target_dir / "README.md")

    # Copy root LICENSE
    if ROOT_LICENSE.is_file():
        shutil.copy2(ROOT_LICENSE, target_dir / "LICENSE")

    # Copy assets/logo.svg
    overlay_logo = OVERLAY_DIR / "assets" / "logo.svg"
    if overlay_logo.is_file():
        dest_logo = target_dir / "assets" / "logo.svg"
        dest_logo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(overlay_logo, dest_logo)

    # Copy rules/*.md
    overlay_rules = OVERLAY_DIR / "rules"
    if overlay_rules.is_dir():
        dest_rules = target_dir / "rules"
        dest_rules.mkdir(parents=True, exist_ok=True)
        for rule_file in sorted(overlay_rules.glob("*.md")):
            shutil.copy2(rule_file, dest_rules / rule_file.name)

    # Copy hooks.json
    overlay_hooks = OVERLAY_DIR / "hooks.json"
    if overlay_hooks.is_file():
        shutil.copy2(overlay_hooks, target_dir / "hooks.json")

    # Copy scripts/git_guard.py and set executable permissions
    overlay_guard = OVERLAY_DIR / "scripts" / "git_guard.py"
    if overlay_guard.is_file():
        dest_guard = target_dir / "scripts" / "git_guard.py"
        dest_guard.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(overlay_guard, dest_guard)
        os.chmod(dest_guard, 0o755)

    # Copy overlay skills resources (e.g. antigravity.md and antigravity-dispatch.md)
    overlay_skills = OVERLAY_DIR / "skills"
    if overlay_skills.is_dir():
        for overlay_file in sorted(overlay_skills.rglob("*")):
            if overlay_file.is_file():
                rel = overlay_file.relative_to(overlay_skills)
                dest = target_dir / "skills" / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(overlay_file, dest)


def build_plugin(target_dir: Optional[Path] = None) -> None:
    """Execute complete deterministic Antigravity 2.0 plugin build."""
    out_dir = target_dir or DEFAULT_TARGET_DIR
    print(f"Building Antigravity 2.0 plugin at: {out_dir}")

    # Clean target directory
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    patches_by_file = load_patches()
    print(f"Loaded {len(patches_by_file)} upstream patches from patches.toml")

    # 1. Manifest
    build_manifest(out_dir)
    print("Generated plugin.json manifest")

    # 2. Agents
    build_agents(out_dir, patches_by_file)
    agent_count = len(list((out_dir / "agents").glob("*.md")))
    print(f"Generated {agent_count} agents in agents/")

    # 3. Skills
    build_skills(out_dir, patches_by_file)
    skill_count = len([p for p in (out_dir / "skills").iterdir() if p.is_dir()])
    print(f"Generated {skill_count} skills in skills/")

    # 4. Overlay & Assets
    copy_overlay_and_assets(out_dir)
    print("Injected overlay rules, guides, assets, hooks, and LICENSE")

    # Final permission verification
    guard_script = out_dir / "scripts" / "git_guard.py"
    if guard_script.is_file():
        os.chmod(guard_script, 0o755)
        print(f"Set 0755 permissions on {guard_script}")

    print("Antigravity 2.0 build completed successfully.")


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    try:
        build_plugin(target)
    except Exception as exc:
        print(f"Build failed with error: {exc}", file=sys.stderr)
        sys.exit(1)
