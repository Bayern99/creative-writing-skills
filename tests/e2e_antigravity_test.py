#!/usr/bin/env python3
"""Comprehensive 4-Tier Opaque-Box E2E Test Suite for creative-writing-skills Antigravity 2.0 Plugin.

Authoritative Requirements & Specifications:
- ORIGINAL_REQUEST.md:
    * User model directive: muse = inherit, all 14 subagents = flash (Gemini 3.8 Flash).
    * Subagents differentiated by specialized system prompt and skill bundles.
    * 0 errors and 0 warnings with `agy plugin validate --strict`.
    * Native multi-agent orchestration via `invoke_subagent`.
- PROJECT.md:
    * 15 agents: muse (orchestrator), writer, character-sim, outliner, critic, brainstormer,
      continuity-checker, reader-sim, style-creator, creative-researcher, kb-lead, explorer,
      session-miner, cold-reader, kb-maintainer.
    * 28 skills from upstream closure (12 native, 15 meridian-base, 1 writing-sync).
    * Overlay assets, rules (story-project.md, kb-pages.md), hooks.json, and git_guard.py.
    * Complete elimination of Claude/Mars artifacts (opus, sonnet, argon, disallowedTools, etc.).
- spec_miner_antigravity/handoff.md:
    * Strict RFC 8259 JSON format for plugin.json (no comments or trailing commas).
    * Semver version, strict kebab-case plugin name, relative logo path, max 3 suggestedPrompts.
    * Agent frontmatter schema: name, description, model (inherit/flash/flash_lite/pro),
      commandExecutionPolicy (sandbox/auto), mainAgent (bool), subagent (bool).
    * SKILL.md and rule markdown body size <= 24,000 bytes.
    * Hooks: grouped PreToolUse format with matcher and hooks list pointing to executable command.

Test Tier Architecture:
- Tier 1: Feature Coverage (Core feature isolation: manifest, agents.toml, agent frontmatter, skills, rules & hooks)
- Tier 2: Boundary & Corner Cases (Strict JSON parsing, model tier bounds, file length caps, tool stripping, git guard edge cases)
- Tier 3: Cross-Feature Combinations (Agent topology, referential closure, patches SHA-256 validation, prompt constraints, rules & globs)
- Tier 4: Real-World Scenarios (Isolated HOME installation, CLI discovery via agy plugin list & agy agents, lifecycle, workflow simulation)
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Base repository paths
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CLAUDE_DIR = REPO_ROOT / "plugin" / "claude"
CONFIG_AGENTS_TOML = REPO_ROOT / "antigravity" / "agents.toml"
CONFIG_PATCHES_TOML = REPO_ROOT / "antigravity" / "patches.toml"
OVERLAY_DIR = REPO_ROOT / "antigravity" / "overlay"
OVERLAY_MANIFEST_TMPL = OVERLAY_DIR / "plugin.json.tmpl"
OVERLAY_LOGO = OVERLAY_DIR / "assets" / "logo.svg"
OVERLAY_RULES_DIR = OVERLAY_DIR / "rules"
OVERLAY_HOOKS_JSON = OVERLAY_DIR / "hooks.json"
OVERLAY_GIT_GUARD = OVERLAY_DIR / "scripts" / "git_guard.py"

TARGET_PLUGIN_DIR = REPO_ROOT / "plugin" / "antigravity"
TARGET_MANIFEST = TARGET_PLUGIN_DIR / "plugin.json"
TARGET_AGENTS_DIR = TARGET_PLUGIN_DIR / "agents"
TARGET_SKILLS_DIR = TARGET_PLUGIN_DIR / "skills"
TARGET_RULES_DIR = TARGET_PLUGIN_DIR / "rules"
TARGET_HOOKS_JSON = TARGET_PLUGIN_DIR / "hooks.json"
TARGET_GIT_GUARD = TARGET_PLUGIN_DIR / "scripts" / "git_guard.py"

# Canonical specifications
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

ALLOWED_MODEL_TIERS = {"inherit", "flash", "flash_lite", "pro"}
DISALLOWED_MODEL_STRINGS = {
    "opus",
    "sonnet",
    "argon",
    "luna",
    "gemini-3.8-flash",
    "gpt-4",
    "claude-3-opus",
    "claude-3-5-sonnet",
}


def parse_yaml_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter between initial '---' markers and return (metadata, body)."""
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, content

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    yaml_text = "".join(lines[1:end_idx])
    body = "".join(lines[end_idx + 1 :])

    try:
        import yaml
        loaded = yaml.safe_load(yaml_text)
        if isinstance(loaded, dict):
            return loaded, body
    except Exception:
        pass

    # Simple fallback YAML parser for basic key-value frontmatter
    metadata: Dict[str, Any] = {}
    current_key = None
    in_list = False

    for line in yaml_text.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        # Check list item
        if trimmed.startswith("- ") and current_key:
            item_val = trimmed[2:].strip().strip("\"'")
            if current_key not in metadata or not isinstance(metadata[current_key], list):
                metadata[current_key] = []
            metadata[current_key].append(item_val)
            continue

        # Check key: value
        if ":" in trimmed:
            key, val = trimmed.split(":", 1)
            key = key.strip()
            val = val.strip()

            if val == "":
                current_key = key
                metadata[key] = []
                in_list = True
            elif val.lower() == "true":
                metadata[key] = True
                current_key = key
                in_list = False
            elif val.lower() == "false":
                metadata[key] = False
                current_key = key
                in_list = False
            elif val.isdigit():
                metadata[key] = int(val)
                current_key = key
                in_list = False
            elif (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                metadata[key] = val[1:-1]
                current_key = key
                in_list = False
            elif val.startswith("[") and val.endswith("]"):
                # Inline list
                raw_items = val[1:-1].split(",")
                metadata[key] = [item.strip().strip("\"'") for item in raw_items if item.strip()]
                current_key = key
                in_list = False
            else:
                metadata[key] = val
                current_key = key
                in_list = False

    return metadata, body


def get_git_guard_executable() -> Optional[Path]:
    """Return path to git_guard.py from target plugin or overlay."""
    if TARGET_GIT_GUARD.exists():
        return TARGET_GIT_GUARD
    if OVERLAY_GIT_GUARD.exists():
        return OVERLAY_GIT_GUARD
    return None


def get_active_manifest_path() -> Optional[Path]:
    """Return path to active plugin manifest (target plugin.json or overlay template)."""
    if TARGET_MANIFEST.exists():
        return TARGET_MANIFEST
    if OVERLAY_MANIFEST_TMPL.exists():
        return OVERLAY_MANIFEST_TMPL
    return None


# ==============================================================================
# Tier 1: Feature Coverage (Core Isolation Tests)
# ==============================================================================
class Tier1FeatureCoverageTests(unittest.TestCase):
    """Test each core feature in isolation with positive equivalence checks."""

    def test_t1_01_manifest_source_or_target_exists(self):
        """Manifest file exists in target plugin or overlay template."""
        manifest_path = get_active_manifest_path()
        self.assertIsNotNone(
            manifest_path,
            f"Neither {TARGET_MANIFEST} nor {OVERLAY_MANIFEST_TMPL} exists.",
        )
        self.assertTrue(manifest_path.is_file(), f"Manifest {manifest_path} is not a file.")

    def test_t1_02_manifest_valid_json_strict(self):
        """Manifest parses cleanly via standard json.loads enforcing strict JSON."""
        manifest_path = get_active_manifest_path()
        self.assertIsNotNone(manifest_path, "Manifest path is not available.")
        raw_text = manifest_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw_text)
            self.assertIsInstance(data, dict, "Manifest root must be a JSON object.")
        except json.JSONDecodeError as exc:
            self.fail(f"Manifest failed strict JSON decoding: {exc}")

    def test_t1_03_manifest_core_identity(self):
        """Manifest defines valid name, semver version, displayName, and description."""
        manifest_path = get_active_manifest_path()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(data.get("name"), "creative-writing-skills")
        # Strict kebab-case check
        self.assertRegex(
            data["name"],
            r"^[a-z0-9]+(-[a-z0-9]+)*$",
            f"Plugin name '{data['name']}' must be strict kebab-case.",
        )
        # Semver check
        self.assertIn("version", data)
        self.assertRegex(
            data["version"],
            r"^\d+\.\d+\.\d+",
            f"Plugin version '{data['version']}' must follow semver.",
        )
        self.assertTrue(data.get("displayName"), "Manifest missing non-empty displayName.")
        self.assertTrue(data.get("description"), "Manifest missing non-empty description.")

    def test_t1_04_manifest_logo_relative(self):
        """Manifest specifies relative logo path pointing to an existing file."""
        manifest_path = get_active_manifest_path()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        logo_rel = data.get("logo")
        self.assertIsNotNone(logo_rel, "Manifest missing 'logo' property.")
        self.assertFalse(
            logo_rel.startswith("/"),
            f"Logo '{logo_rel}' must be relative, not absolute.",
        )
        self.assertFalse(
            logo_rel.startswith("http"),
            f"Logo '{logo_rel}' must be a local asset, not a web URL.",
        )

        # File must exist either in target plugin or in overlay
        logo_in_target = TARGET_PLUGIN_DIR / logo_rel
        logo_in_overlay = OVERLAY_DIR / logo_rel
        self.assertTrue(
            logo_in_target.exists() or logo_in_overlay.exists(),
            f"Logo file '{logo_rel}' not found at {logo_in_target} or {logo_in_overlay}.",
        )

    def test_t1_05_manifest_suggested_prompts_bounds(self):
        """Manifest suggestedPrompts is a list of strings with 1 to 3 items."""
        manifest_path = get_active_manifest_path()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        prompts = data.get("suggestedPrompts")
        self.assertIsInstance(prompts, list, "suggestedPrompts must be an array.")
        self.assertGreaterEqual(len(prompts), 1, "suggestedPrompts must have at least 1 prompt.")
        self.assertLessEqual(
            len(prompts),
            3,
            f"suggestedPrompts has {len(prompts)} prompts; Antigravity limits display to 3.",
        )
        for p in prompts:
            self.assertIsInstance(p, str, "Each suggested prompt must be a string.")
            self.assertGreater(len(p.strip()), 5, f"Prompt '{p}' is suspiciously short.")

    def test_t1_06_manifest_secure_urls(self):
        """Manifest homepage and repository URLs use secure HTTPS protocol."""
        manifest_path = get_active_manifest_path()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for field in ("homepage", "repository"):
            url = data.get(field)
            if url:
                self.assertTrue(
                    url.startswith("https://"),
                    f"Manifest {field} '{url}' must use HTTPS.",
                )

    def test_t1_07_agents_toml_exists_and_parses(self):
        """Configuration file antigravity/agents.toml exists and parses cleanly."""
        self.assertTrue(
            CONFIG_AGENTS_TOML.is_file(),
            f"agents.toml not found at {CONFIG_AGENTS_TOML}.",
        )
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        self.assertIn("agents", config, "agents.toml must declare [agents] table.")

    def test_t1_08_muse_model_is_inherit(self):
        """User Directive: muse agent model must be configured to 'inherit'."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        muse_cfg = config.get("agents", {}).get("muse", {})
        self.assertEqual(
            muse_cfg.get("model"),
            "inherit",
            f"User Directive Violation: muse model must be 'inherit', got '{muse_cfg.get('model')}'.",
        )

    def test_t1_09_all_subagents_model_is_flash(self):
        """User Directive: all 14 subagents must be configured to 'flash'."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        defaults = config.get("defaults", {})
        default_model = defaults.get("model")
        agents_table = config.get("agents", {})

        for name in EXPECTED_AGENTS:
            if name == "muse":
                continue
            agent_cfg = agents_table.get(name, {})
            model = agent_cfg.get("model", default_model)
            self.assertEqual(
                model,
                "flash",
                f"User Directive Violation: subagent '{name}' must have model 'flash', got '{model}'.",
            )

    def test_t1_10_command_execution_policy_sandbox(self):
        """agents.toml enforces commandExecutionPolicy = 'sandbox'."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        defaults = config.get("defaults", {})
        self.assertEqual(
            defaults.get("commandExecutionPolicy"),
            "sandbox",
            f"Default commandExecutionPolicy must be 'sandbox', got '{defaults.get('commandExecutionPolicy')}'.",
        )

    def test_t1_11_all_15_agents_declared_in_config(self):
        """agents.toml explicitly declares configurations for all 15 agents."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        agents_table = config.get("agents", {})
        missing = [a for a in EXPECTED_AGENTS if a not in agents_table]
        self.assertEqual(
            missing,
            [],
            f"Missing agent definitions in agents.toml: {missing}",
        )

    def test_t1_12_all_15_target_agent_files_exist(self):
        """All 15 agent markdown files exist in plugin/antigravity/agents/ (M3 deliverable)."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"Target agents directory {TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        found = [p.stem for p in TARGET_AGENTS_DIR.glob("*.md")]
        missing = [a for a in EXPECTED_AGENTS if a not in found]
        self.assertEqual(missing, [], f"Missing agent files in {TARGET_AGENTS_DIR}: {missing}")

    def test_t1_13_agent_frontmatter_name_matches_stem(self):
        """Every target agent frontmatter name exactly matches its filename stem."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
            self.assertEqual(
                fm.get("name"),
                path.stem,
                f"Agent {path.name} frontmatter name '{fm.get('name')}' != '{path.stem}'.",
            )

    def test_t1_14_agent_frontmatter_description_non_empty(self):
        """Every target agent frontmatter contains a non-empty description."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
            desc = fm.get("description", "")
            self.assertTrue(
                isinstance(desc, str) and len(desc.strip()) > 10,
                f"Agent {path.name} has invalid/empty description: {desc!r}",
            )

    def test_t1_15_agent_main_agent_flags(self):
        """Target agents have mainAgent: true only for muse, writer, character-sim, outliner."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
            is_main = fm.get("mainAgent") is True
            expected_main = path.stem in ENTRY_AGENTS
            self.assertEqual(
                is_main,
                expected_main,
                f"Agent {path.stem} mainAgent flag expected {expected_main}, got {is_main}.",
            )

    def test_t1_16_agent_subagent_flags(self):
        """Target agents have subagent: false for muse, subagent: true for all 14 others."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
            is_sub = fm.get("subagent") is True
            expected_sub = path.stem != "muse"
            self.assertEqual(
                is_sub,
                expected_sub,
                f"Agent {path.stem} subagent flag expected {expected_sub}, got {is_sub}.",
            )

    def test_t1_17_all_28_skills_present(self):
        """All 28 skill directories are present in plugin/antigravity/skills/ (M3 deliverable)."""
        if not TARGET_SKILLS_DIR.exists():
            self.assertTrue(
                TARGET_SKILLS_DIR.exists(),
                f"{TARGET_SKILLS_DIR} does not exist yet (M3 pending).",
            )
        present = [p.name for p in TARGET_SKILLS_DIR.iterdir() if p.is_dir()]
        missing = [s for s in EXPECTED_SKILLS if s not in present]
        self.assertEqual(missing, [], f"Missing skills in {TARGET_SKILLS_DIR}: {missing}")

    def test_t1_18_skill_md_name_matches_folder(self):
        """Every skill SKILL.md frontmatter name matches its containing directory name."""
        skills_dir = (
            TARGET_SKILLS_DIR
            if TARGET_SKILLS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "skills"
        )
        self.assertTrue(skills_dir.exists(), f"Skills directory not found at {skills_dir}")
        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir():
                continue
            skill_md = skill_path / "SKILL.md"
            self.assertTrue(
                skill_md.is_file(),
                f"Skill directory {skill_path.name} missing SKILL.md",
            )
            fm, _ = parse_yaml_frontmatter(skill_md.read_text(encoding="utf-8"))
            self.assertEqual(
                fm.get("name"),
                skill_path.name,
                f"SKILL.md in {skill_path.name} has name '{fm.get('name')}', expected '{skill_path.name}'.",
            )

    def test_t1_19_skill_md_description_non_empty(self):
        """Every skill SKILL.md contains a non-empty description for model tool evaluation."""
        skills_dir = (
            TARGET_SKILLS_DIR
            if TARGET_SKILLS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "skills"
        )
        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir():
                continue
            skill_md = skill_path / "SKILL.md"
            fm, _ = parse_yaml_frontmatter(skill_md.read_text(encoding="utf-8"))
            desc = fm.get("description", "")
            self.assertTrue(
                isinstance(desc, str) and len(desc.strip()) > 10,
                f"Skill {skill_path.name} missing substantive description: {desc!r}",
            )

    def test_t1_20_skill_key_resources_retained(self):
        """Key skill resource directories and files are retained in target/source."""
        skills_dir = (
            TARGET_SKILLS_DIR
            if TARGET_SKILLS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "skills"
        )
        key_files = [
            skills_dir / "creative-writing-craft" / "resources" / "prose-modes.md",
            skills_dir / "writing-principles" / "resources" / "antipatterns.md",
            skills_dir / "story-planning" / "resources" / "story-architecture.md",
        ]
        for kf in key_files:
            self.assertTrue(kf.is_file(), f"Key skill resource missing: {kf}")

    def test_t1_21_skill_disable_model_invocation_flags(self):
        """Manual/setup skills maintain disable-model-invocation: true."""
        skills_dir = (
            TARGET_SKILLS_DIR
            if TARGET_SKILLS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "skills"
        )
        manual_skills = [
            "creative-writing-muse",
            "project-setup",
            "qi-maintenance",
            "reflect",
        ]
        for name in manual_skills:
            skill_md = skills_dir / name / "SKILL.md"
            if skill_md.exists():
                fm, _ = parse_yaml_frontmatter(skill_md.read_text(encoding="utf-8"))
                self.assertTrue(
                    fm.get("disable-model-invocation") is True,
                    f"Skill {name} expected disable-model-invocation: true, got {fm.get('disable-model-invocation')}.",
                )

    def test_t1_22_rules_files_exist(self):
        """Rules files story-project.md and kb-pages.md exist."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        self.assertTrue(rules_dir.exists(), f"Rules directory not found at {rules_dir}")
        self.assertTrue(
            (rules_dir / "story-project.md").is_file(),
            f"story-project.md missing in {rules_dir}",
        )
        self.assertTrue(
            (rules_dir / "kb-pages.md").is_file(),
            f"kb-pages.md missing in {rules_dir}",
        )

    def test_t1_23_rule_story_project_trigger(self):
        """story-project.md specifies trigger: model_decision and non-empty description."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        path = rules_dir / "story-project.md"
        fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual(
            fm.get("trigger"),
            "model_decision",
            f"story-project.md expected trigger: model_decision, got '{fm.get('trigger')}'.",
        )
        self.assertTrue(
            fm.get("description"),
            "story-project.md missing description in frontmatter.",
        )

    def test_t1_24_rule_kb_pages_trigger(self):
        """kb-pages.md specifies trigger: glob and globs covering kb/ and work/."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        path = rules_dir / "kb-pages.md"
        fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual(
            fm.get("trigger"),
            "glob",
            f"kb-pages.md expected trigger: glob, got '{fm.get('trigger')}'.",
        )
        globs = fm.get("globs", "")
        self.assertIn("kb/", globs, f"kb-pages.md globs must cover kb/**: got {globs!r}")
        self.assertIn("work/", globs, f"kb-pages.md globs must cover work/**: got {globs!r}")

    def test_t1_25_hooks_json_structure(self):
        """hooks.json defines PreToolUse hook intercepting run_command."""
        hooks_path = (
            TARGET_HOOKS_JSON if TARGET_HOOKS_JSON.exists() else OVERLAY_HOOKS_JSON
        )
        self.assertTrue(hooks_path.is_file(), f"hooks.json missing at {hooks_path}")
        data = json.loads(hooks_path.read_text(encoding="utf-8"))
        guard_cfg = data.get("git-guard") or data.get("git_guard") or next(iter(data.values()), {})
        self.assertIn("PreToolUse", guard_cfg, "hooks.json missing PreToolUse event.")
        pre_tool = guard_cfg["PreToolUse"]
        self.assertIsInstance(pre_tool, list, "PreToolUse must be a list of grouped matcher hooks.")
        self.assertEqual(pre_tool[0].get("matcher"), "run_command")
        self.assertIn("hooks", pre_tool[0])

    def test_t1_26_git_guard_script_executable(self):
        """git_guard.py exists and has executable permissions (0755)."""
        script_path = get_git_guard_executable()
        self.assertIsNotNone(script_path, "git_guard.py not found in target or overlay.")
        self.assertTrue(script_path.is_file(), f"{script_path} is not a file.")
        self.assertTrue(
            os.access(script_path, os.X_OK),
            f"git_guard.py at {script_path} is not executable (chmod +x required).",
        )


# ==============================================================================
# Tier 2: Boundary & Corner Cases (Strict Constraints, Caps & Rejection)
# ==============================================================================
class Tier2BoundaryCornerCaseTests(unittest.TestCase):
    """Test boundary conditions, strict JSON formatting, file length caps, and edge inputs."""

    def test_t2_01_manifest_rejects_json_comments(self):
        """Manifest contains zero JSONC comments (// or /*) to ensure agy plugin install compatibility."""
        manifest_path = get_active_manifest_path()
        content = manifest_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            self.assertFalse(
                stripped.startswith("//"),
                f"Manifest contains line comment: {line}",
            )
            self.assertFalse(
                stripped.startswith("/*"),
                f"Manifest contains block comment: {line}",
            )

    def test_t2_02_manifest_rejects_trailing_commas(self):
        """Manifest contains no trailing commas before closing braces or brackets."""
        manifest_path = get_active_manifest_path()
        content = manifest_path.read_text(encoding="utf-8")
        self.assertNotRegex(
            content,
            r",\s*[}\]]",
            "Manifest contains trailing comma before closing brace/bracket.",
        )

    def test_t2_03_manifest_suggested_prompts_upper_bound(self):
        """suggestedPrompts strictly caps at 3 items (4 causes agy plugin validate warning)."""
        manifest_path = get_active_manifest_path()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        prompts = data.get("suggestedPrompts", [])
        self.assertLessEqual(
            len(prompts),
            3,
            f"Upper boundary violated: suggestedPrompts has {len(prompts)} prompts (>3 triggers CLI warning).",
        )

    def test_t2_04_manifest_no_unknown_top_level_fields(self):
        """Manifest contains no unrecognized top-level keys that trigger validate warnings."""
        allowed_keys = {
            "$schema",
            "name",
            "displayName",
            "version",
            "description",
            "logo",
            "suggestedPrompts",
            "author",
            "homepage",
            "repository",
            "license",
            "keywords",
            "disabled",
        }
        manifest_path = get_active_manifest_path()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        extra_keys = set(data.keys()) - allowed_keys
        self.assertEqual(
            extra_keys,
            set(),
            f"Manifest contains unrecognized top-level keys that trigger warnings in --strict: {extra_keys}",
        )

    def test_t2_05_manifest_no_absolute_paths_in_logo(self):
        """Logo asset path does not use absolute path syntax."""
        manifest_path = get_active_manifest_path()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        logo = data.get("logo", "")
        self.assertFalse(logo.startswith("/"), f"Logo '{logo}' cannot be an absolute path.")
        self.assertFalse(
            bool(re.match(r"^[A-Za-z]:", logo)),
            f"Logo '{logo}' cannot have Windows drive letter.",
        )

    def test_t2_06_no_claude_opus_models(self):
        """Zero agents specify Claude 'opus' tier in agents.toml or target agent frontmatter."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        for name, cfg in config.get("agents", {}).items():
            model = cfg.get("model")
            self.assertNotEqual(
                model,
                "opus",
                f"Agent '{name}' has invalid model tier 'opus' in agents.toml",
            )

        if TARGET_AGENTS_DIR.exists():
            for path in TARGET_AGENTS_DIR.glob("*.md"):
                fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
                self.assertNotEqual(
                    fm.get("model"),
                    "opus",
                    f"Agent {path.name} frontmatter has forbidden model 'opus'.",
                )

    def test_t2_07_no_claude_sonnet_models(self):
        """Zero agents specify Claude 'sonnet' tier."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        for name, cfg in config.get("agents", {}).items():
            self.assertNotEqual(
                cfg.get("model"),
                "sonnet",
                f"Agent '{name}' has forbidden model 'sonnet' in agents.toml",
            )

    def test_t2_08_no_mars_argon_or_luna_models(self):
        """Zero agents specify internal Mars models 'argon' or 'luna'."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        for name, cfg in config.get("agents", {}).items():
            self.assertNotIn(
                cfg.get("model"),
                {"argon", "luna"},
                f"Agent '{name}' has forbidden Mars model identifier.",
            )

    def test_t2_09_no_invalid_model_strings(self):
        """Zero agents specify raw Gemini string 'gemini-3.8-flash' (must use tier name 'flash')."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        for name, cfg in config.get("agents", {}).items():
            self.assertNotEqual(
                cfg.get("model"),
                "gemini-3.8-flash",
                f"Agent '{name}' specifies 'gemini-3.8-flash' (fails CLI validator; must use 'flash').",
            )

    def test_t2_10_model_tier_validator_conformance(self):
        """All declared models belong strictly to Antigravity recognized tiers."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        default_model = config.get("defaults", {}).get("model")
        if default_model:
            self.assertIn(
                default_model,
                ALLOWED_MODEL_TIERS,
                f"Default model '{default_model}' is not in allowed tiers {ALLOWED_MODEL_TIERS}.",
            )

        for name, cfg in config.get("agents", {}).items():
            model = cfg.get("model", default_model)
            self.assertIn(
                model,
                ALLOWED_MODEL_TIERS,
                f"Agent '{name}' model '{model}' is not in allowed tiers {ALLOWED_MODEL_TIERS}.",
            )

    def test_t2_11_skill_md_body_under_24k_bytes(self):
        """All 28 SKILL.md body contents are strictly <= 24,000 bytes (prevents validator cutoff warning)."""
        skills_dir = (
            TARGET_SKILLS_DIR
            if TARGET_SKILLS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "skills"
        )
        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir():
                continue
            skill_md = skill_path / "SKILL.md"
            _, body = parse_yaml_frontmatter(skill_md.read_text(encoding="utf-8"))
            body_bytes = len(body.encode("utf-8"))
            self.assertLessEqual(
                body_bytes,
                24000,
                f"Skill '{skill_path.name}' body is {body_bytes} bytes (>24000 byte limit causes validator warning).",
            )

    def test_t2_12_rule_files_under_24k_bytes(self):
        """All rule files are strictly <= 24,000 bytes."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        for rule_path in rules_dir.glob("*.md"):
            size = rule_path.stat().st_size
            self.assertLessEqual(
                size,
                24000,
                f"Rule '{rule_path.name}' size is {size} bytes (>24000 limit).",
            )

    def test_t2_13_agent_prompts_not_truncated(self):
        """All agent prompt bodies contain substantive guidance (> 100 bytes)."""
        agents_dir = (
            TARGET_AGENTS_DIR
            if TARGET_AGENTS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "agents"
        )
        for agent_path in agents_dir.glob("*.md"):
            _, body = parse_yaml_frontmatter(agent_path.read_text(encoding="utf-8"))
            body_len = len(body.strip().encode("utf-8"))
            self.assertGreater(
                body_len,
                100,
                f"Agent '{agent_path.name}' prompt body appears empty or truncated ({body_len} bytes).",
            )

    def test_t2_14_overlay_guides_size_bounds(self):
        """Overlay setup and dispatch guides are well-formed and under 24,000 bytes."""
        guides = [
            OVERLAY_DIR / "skills" / "project-setup" / "resources" / "antigravity.md",
            OVERLAY_DIR / "skills" / "writing-staffing" / "resources" / "antigravity-dispatch.md",
        ]
        for g in guides:
            self.assertTrue(g.is_file(), f"Overlay guide missing at {g}")
            size = g.stat().st_size
            self.assertGreater(size, 200, f"Guide {g.name} is suspiciously short.")
            self.assertLessEqual(size, 24000, f"Guide {g.name} exceeds 24,000 bytes.")

    def test_t2_15_logo_asset_size_and_format(self):
        """logo.svg is valid XML vector graphic under 100 KB."""
        logo_path = (
            TARGET_PLUGIN_DIR / "assets" / "logo.svg"
            if (TARGET_PLUGIN_DIR / "assets" / "logo.svg").exists()
            else OVERLAY_LOGO
        )
        self.assertTrue(logo_path.is_file(), f"logo.svg missing at {logo_path}")
        size = logo_path.stat().st_size
        self.assertLess(size, 100 * 1024, f"logo.svg exceeds 100 KB ({size} bytes).")
        content = logo_path.read_text(encoding="utf-8")
        self.assertIn("<svg", content, "logo.svg missing <svg> element.")
        self.assertIn("</svg>", content, "logo.svg missing closing </svg> tag.")

    def test_t2_16_no_disallowed_tools_in_frontmatter(self):
        """Target agent frontmatters contain zero 'disallowedTools' blocks (Claude-specific)."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "disallowedTools:",
                content,
                f"Agent {path.name} contains residual Claude 'disallowedTools:' frontmatter block.",
            )

    def test_t2_17_no_ask_user_question_tool_reference(self):
        """Target agent frontmatters contain zero references to 'AskUserQuestion'."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
            tools = fm.get("tools", [])
            self.assertNotIn(
                "AskUserQuestion",
                tools,
                f"Agent {path.name} declares Claude-specific tool AskUserQuestion.",
            )

    def test_t2_18_no_notebook_edit_tool_reference(self):
        """Target agent frontmatters contain zero references to 'NotebookEdit'."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
            tools = fm.get("tools", [])
            self.assertNotIn(
                "NotebookEdit",
                tools,
                f"Agent {path.name} declares Claude-specific tool NotebookEdit.",
            )

    def test_t2_19_no_effort_field_in_frontmatter(self):
        """Target agent frontmatters contain zero 'effort:' fields."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for path in TARGET_AGENTS_DIR.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
            self.assertNotIn(
                "effort",
                fm,
                f"Agent {path.name} contains Claude-specific 'effort' frontmatter.",
            )

    def test_t2_20_command_execution_policy_allowed_values(self):
        """commandExecutionPolicy is strictly 'sandbox' or 'auto' (other values cause fatal error)."""
        if TARGET_AGENTS_DIR.exists():
            for path in TARGET_AGENTS_DIR.glob("*.md"):
                fm, _ = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
                policy = fm.get("commandExecutionPolicy")
                if policy:
                    self.assertIn(
                        policy,
                        {"sandbox", "auto"},
                        f"Agent {path.name} has invalid policy '{policy}' (only sandbox/auto allowed).",
                    )

    def _execute_git_guard(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        script = get_git_guard_executable()
        self.assertIsNotNone(script, "git_guard.py not found.")
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=5,
        )
        self.assertEqual(proc.returncode, 0, f"git_guard crashed: {proc.stderr}")
        return json.loads(proc.stdout.strip())

    def test_t2_21_git_guard_blocks_git_reset_hard(self):
        """git_guard responds decision: ask for 'git reset --hard HEAD~1'."""
        payload = {
            "toolCall": {
                "tool": "run_command",
                "args": {"CommandLine": "git reset --hard HEAD~1"},
            }
        }
        res = self._execute_git_guard(payload)
        self.assertEqual(
            res.get("decision"),
            "ask",
            f"Expected ask for git reset --hard, got {res}",
        )

    def test_t2_22_git_guard_blocks_git_clean(self):
        """git_guard responds decision: ask for 'git clean -fd'."""
        payload = {
            "toolCall": {
                "tool": "run_command",
                "args": {"CommandLine": "git clean -fd"},
            }
        }
        res = self._execute_git_guard(payload)
        self.assertEqual(
            res.get("decision"),
            "ask",
            f"Expected ask for git clean, got {res}",
        )

    def test_t2_23_git_guard_blocks_git_restore(self):
        """git_guard responds decision: ask for 'git restore .'."""
        payload = {
            "toolCall": {
                "tool": "run_command",
                "args": {"CommandLine": "git restore ."},
            }
        }
        res = self._execute_git_guard(payload)
        self.assertEqual(
            res.get("decision"),
            "ask",
            f"Expected ask for git restore, got {res}",
        )

    def test_t2_24_git_guard_blocks_git_checkout_destructive(self):
        """git_guard responds decision: ask for 'git checkout -- draft.md'."""
        payload = {
            "toolCall": {
                "tool": "run_command",
                "args": {"CommandLine": "git checkout -- draft.md"},
            }
        }
        res = self._execute_git_guard(payload)
        self.assertEqual(
            res.get("decision"),
            "ask",
            f"Expected ask for git checkout --, got {res}",
        )

    def test_t2_25_git_guard_blocks_git_revert(self):
        """git_guard responds decision: ask for 'git revert HEAD'."""
        payload = {
            "toolCall": {
                "tool": "run_command",
                "args": {"CommandLine": "git revert HEAD"},
            }
        }
        res = self._execute_git_guard(payload)
        self.assertEqual(
            res.get("decision"),
            "ask",
            f"Expected ask for git revert, got {res}",
        )

    def test_t2_26_git_guard_allows_safe_git_commands(self):
        """git_guard responds decision: allow for non-destructive git commands."""
        safe_cmds = ["git status", "git diff", "git log -n 5", "git branch"]
        for cmd in safe_cmds:
            payload = {
                "toolCall": {
                    "tool": "run_command",
                    "args": {"CommandLine": cmd},
                }
            }
            res = self._execute_git_guard(payload)
            self.assertEqual(
                res.get("decision"),
                "allow",
                f"Expected allow for safe command '{cmd}', got {res}",
            )

    def test_t2_27_git_guard_handles_empty_or_malformed_input(self):
        """git_guard gracefully handles empty, non-dict, or non-git inputs without crashing."""
        script = get_git_guard_executable()
        self.assertIsNotNone(script, "git_guard.py not found.")

        # Test empty input
        p1 = subprocess.run(
            [sys.executable, str(script)],
            input="",
            text=True,
            capture_output=True,
        )
        self.assertEqual(p1.returncode, 0)
        self.assertEqual(json.loads(p1.stdout.strip()).get("decision"), "allow")

        # Test non-git command
        p2 = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"toolCall": {"args": {"CommandLine": "ls -la"}}}),
            text=True,
            capture_output=True,
        )
        self.assertEqual(p2.returncode, 0)
        self.assertEqual(json.loads(p2.stdout.strip()).get("decision"), "allow")


# ==============================================================================
# Tier 3: Cross-Feature Combinations & Interface Contracts
# ==============================================================================
class Tier3CrossFeatureCombinationTests(unittest.TestCase):
    """Test interactions between agents, skills, rules, patches, and runtime contracts."""

    def test_t3_01_orchestrator_subagent_exclusion(self):
        """muse agent is exclusively mainAgent=true, subagent=false (hub cannot be called as subagent)."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        muse = config.get("agents", {}).get("muse", {})
        self.assertTrue(muse.get("mainAgent") is True)
        self.assertTrue(muse.get("subagent") is False)

    def test_t3_02_dual_mode_agents(self):
        """writer, character-sim, outliner have both mainAgent=true and subagent=true."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        agents = config.get("agents", {})
        for name in ("writer", "character-sim", "outliner"):
            cfg = agents.get(name, {})
            self.assertTrue(
                cfg.get("mainAgent") is True,
                f"Dual-mode agent {name} must have mainAgent: true",
            )
            self.assertTrue(
                cfg.get("subagent") is True,
                f"Dual-mode agent {name} must have subagent: true",
            )

    def test_t3_03_pure_subagents_exclusion_from_main(self):
        """All 11 specialized subagents have mainAgent=false and subagent=true."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        agents = config.get("agents", {})
        for name in SUBAGENT_ONLY:
            cfg = agents.get(name, {})
            self.assertFalse(
                cfg.get("mainAgent") is True,
                f"Specialized subagent {name} must NOT have mainAgent: true",
            )
            self.assertTrue(
                cfg.get("subagent") is True,
                f"Specialized subagent {name} must have subagent: true",
            )

    def test_t3_04_subagent_spawning_graph_consistency(self):
        """All subagents declared in muse.subagents exist in EXPECTED_AGENTS and have subagent=true."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        muse_subs = config.get("agents", {}).get("muse", {}).get("subagents", [])
        self.assertGreater(len(muse_subs), 5, "muse must declare delegatable subagents.")
        for sub_name in muse_subs:
            self.assertIn(
                sub_name,
                EXPECTED_AGENTS,
                f"muse references unknown subagent '{sub_name}'.",
            )
            sub_cfg = config.get("agents", {}).get(sub_name, {})
            self.assertTrue(
                sub_cfg.get("subagent") is True,
                f"Subagent '{sub_name}' referenced by muse does not have subagent: true.",
            )

    def test_t3_05_kb_lead_subagent_hierarchy(self):
        """kb-lead delegates exclusively to explorer, session-miner, cold-reader, kb-maintainer."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        kb_lead_subs = (
            config.get("agents", {}).get("kb-lead", {}).get("subagents", [])
        )
        expected_subs = {
            "explorer",
            "session-miner",
            "cold-reader",
            "kb-maintainer",
        }
        self.assertEqual(
            set(kb_lead_subs),
            expected_subs,
            f"kb-lead subagent graph mismatch: expected {expected_subs}, got {set(kb_lead_subs)}",
        )

    def test_t3_06_agent_skills_exist_in_plugin_skills(self):
        """Every skill referenced in agents.toml [agents.*.skills] exists in the 28 skills closure."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        for agent_name, cfg in config.get("agents", {}).items():
            for skill_ref in cfg.get("skills", []):
                skill_name = skill_ref.replace("skills/", "")
                self.assertIn(
                    skill_name,
                    EXPECTED_SKILLS,
                    f"Agent '{agent_name}' references non-existent skill '{skill_name}'.",
                )

    def test_t3_07_agent_optional_skills_exist(self):
        """Every optional skill referenced in agents.toml exists in the 28 skills closure."""
        with open(CONFIG_AGENTS_TOML, "rb") as fp:
            config = tomllib.load(fp)
        for agent_name, cfg in config.get("agents", {}).items():
            for skill_ref in cfg.get("optional_skills", []):
                skill_name = skill_ref.replace("skills/", "")
                self.assertIn(
                    skill_name,
                    EXPECTED_SKILLS,
                    f"Agent '{agent_name}' references non-existent optional skill '{skill_name}'.",
                )

    def test_t3_08_all_28_skills_accounted_for(self):
        """The total inventory of skills matches the 28 closure skills exactly."""
        skills_dir = (
            TARGET_SKILLS_DIR
            if TARGET_SKILLS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "skills"
        )
        found_skills = sorted(
            [p.name for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
        )
        self.assertEqual(
            found_skills,
            sorted(EXPECTED_SKILLS),
            f"Skill inventory mismatch: {set(found_skills) ^ set(EXPECTED_SKILLS)}",
        )

    def test_t3_09_skill_references_syntax_clean(self):
        """Zero occurrences of Claude package prefix '/creative-writing-skills:' in converted files."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"{TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        prefix = "/creative-writing-skills:"
        violations = []
        for root, _, files in os.walk(TARGET_PLUGIN_DIR):
            for file in files:
                if not file.endswith(".md"):
                    continue
                path = Path(root) / file
                if prefix in path.read_text(encoding="utf-8", errors="ignore"):
                    violations.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            violations,
            [],
            f"Residual Claude skill prefix '{prefix}' found in files: {violations}",
        )

    def test_t3_10_no_dangling_markdown_links_in_skills(self):
        """Markdown links inside skill SKILL.md point to actual existing files."""
        skills_dir = (
            TARGET_SKILLS_DIR
            if TARGET_SKILLS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "skills"
        )
        dangling = []
        link_regex = re.compile(r"\[.*?\]\((resources/[^#\)]+)(?:#[^\)]*)?\)")

        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir():
                continue
            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(encoding="utf-8")
            for match in link_regex.finditer(content):
                rel_target = match.group(1)
                target_file = skill_path / rel_target
                if not target_file.exists():
                    dangling.append((skill_path.name, rel_target))

        self.assertEqual(dangling, [], f"Dangling resource links in skills: {dangling}")

    def test_t3_11_patches_toml_syntax_and_structure(self):
        """antigravity/patches.toml exists and parses cleanly via tomllib."""
        self.assertTrue(CONFIG_PATCHES_TOML.is_file(), f"{CONFIG_PATCHES_TOML} missing.")
        with open(CONFIG_PATCHES_TOML, "rb") as fp:
            data = tomllib.load(fp)
        self.assertIn("patches", data, "patches.toml missing [[patches]] array.")
        self.assertGreaterEqual(
            len(data["patches"]),
            6,
            f"Expected at least 6 patches in patches.toml, got {len(data['patches'])}.",
        )

    def test_t3_12_patches_target_files_exist_in_claude_source(self):
        """Every target file declared in patches.toml exists in plugin/claude/."""
        with open(CONFIG_PATCHES_TOML, "rb") as fp:
            data = tomllib.load(fp)
        for patch in data["patches"]:
            target = SOURCE_CLAUDE_DIR / patch["file"]
            self.assertTrue(
                target.is_file(),
                f"Patch target file does not exist in upstream source: {target}",
            )

    def test_t3_13_patches_sha256_checksums_match_upstream(self):
        """Every patch SHA-256 in patches.toml matches the actual upstream file checksum."""
        with open(CONFIG_PATCHES_TOML, "rb") as fp:
            data = tomllib.load(fp)
        for patch in data["patches"]:
            target = SOURCE_CLAUDE_DIR / patch["file"]
            computed = hashlib.sha256(target.read_bytes()).hexdigest()
            expected = patch["sha256"]
            self.assertEqual(
                computed,
                expected,
                f"SHA256 mismatch for patch on {patch['file']}: computed {computed} != expected {expected}",
            )

    def test_t3_14_patches_search_strings_exist_in_upstream(self):
        """Every search string declared in patches.toml exists verbatim in the upstream target file."""
        with open(CONFIG_PATCHES_TOML, "rb") as fp:
            data = tomllib.load(fp)
        for patch in data["patches"]:
            target = SOURCE_CLAUDE_DIR / patch["file"]
            content = target.read_text(encoding="utf-8")
            self.assertIn(
                patch["search"],
                content,
                f"Search block for {patch['file']} was not found verbatim in upstream file.",
            )

    def test_t3_15_patches_replace_strings_contain_antigravity_syntax(self):
        """Every replacement block incorporates native Antigravity syntax and conventions."""
        with open(CONFIG_PATCHES_TOML, "rb") as fp:
            data = tomllib.load(fp)
        for patch in data["patches"]:
            replace_text = patch["replace"]
            # Assert absence of meridian spawn and presence of Antigravity references
            self.assertNotIn("meridian spawn", replace_text)
            self.assertTrue(
                any(
                    term in replace_text
                    for term in (
                        "Antigravity",
                        "antigravity",
                        "invoke_subagent",
                        "flash",
                        "inherit",
                        "transcript.jsonl",
                        ".gemini",
                    )
                ),
                f"Patch replacement for {patch['file']} does not contain Antigravity terminology: {replace_text[:100]}...",
            )

    def test_t3_16_reviewer_agents_have_read_only_constraint(self):
        """Reviewer agents (critic, reader-sim, continuity-checker) have read-only instructions in prompt."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for agent_name in REVIEWER_AGENTS:
            agent_file = TARGET_AGENTS_DIR / f"{agent_name}.md"
            content = agent_file.read_text(encoding="utf-8").lower()
            self.assertTrue(
                any(
                    term in content
                    for term in (
                        "read-only",
                        "writes no files",
                        "do not edit",
                        "write no files",
                        "does not edit",
                        "edits nothing",
                    )
                ),
                f"Reviewer agent {agent_name} lacks explicit read-only prompt constraint.",
            )

    def test_t3_17_subagents_do_not_prompt_user(self):
        """Subagents contain prompt instruction not to prompt the user directly."""
        if not TARGET_AGENTS_DIR.exists():
            self.assertTrue(
                TARGET_AGENTS_DIR.exists(),
                f"{TARGET_AGENTS_DIR} does not exist yet (M3 pending).",
            )
        for agent_name in SUBAGENT_ONLY:
            agent_file = TARGET_AGENTS_DIR / f"{agent_name}.md"
            content = agent_file.read_text(encoding="utf-8").lower()
            self.assertTrue(
                any(
                    term in content
                    for term in (
                        "caller",
                        "do not prompt",
                        "never prompt",
                        "return",
                        "report",
                    )
                ),
                f"Subagent {agent_name} lacks caller-reporting constraint in prompt.",
            )

    def test_t3_18_writer_agent_has_context_retention_instruction(self):
        """writer agent prompt contains instructions for multi-turn revisions and state."""
        agents_dir = (
            TARGET_AGENTS_DIR
            if TARGET_AGENTS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "agents"
        )
        writer_file = agents_dir / "writer.md"
        content = writer_file.read_text(encoding="utf-8").lower()
        self.assertTrue(
            any(
                term in content
                for term in ("revision", "draft", "mode", "prose")
            ),
            "writer agent prompt missing drafting / revision guidance.",
        )

    def test_t3_19_session_miner_points_to_antigravity_transcripts(self):
        """session-miner guidance references Antigravity transcript.jsonl."""
        agents_dir = (
            TARGET_AGENTS_DIR
            if TARGET_AGENTS_DIR.exists()
            else OVERLAY_DIR
        )
        # Check either target agent or patches.toml replace specification
        with open(CONFIG_PATCHES_TOML, "rb") as fp:
            patches = tomllib.load(fp)["patches"]
        miner_patch = next(
            (p for p in patches if "session-miner" in p["file"]), None
        )
        self.assertIsNotNone(miner_patch, "session-miner patch missing in patches.toml")
        self.assertIn("transcript.jsonl", miner_patch["replace"])

    def test_t3_20_style_creator_targets_kb_styles(self):
        """style-creator targets kb styles directory."""
        agents_dir = (
            TARGET_AGENTS_DIR
            if TARGET_AGENTS_DIR.exists()
            else SOURCE_CLAUDE_DIR / "agents"
        )
        style_file = agents_dir / "style-creator.md"
        content = style_file.read_text(encoding="utf-8")
        self.assertTrue(
            "kb/styles" in content or "kb styles" in content or "kb" in content,
            "style-creator must target kb styles directory.",
        )

    def test_t3_21_story_project_rule_has_valid_trigger_and_description(self):
        """story-project.md has trigger: model_decision and non-empty description."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        path = rules_dir / "story-project.md"
        fm, body = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual(fm.get("trigger"), "model_decision")
        self.assertGreater(len(fm.get("description", "")), 15)
        self.assertGreater(len(body), 200)

    def test_t3_22_kb_pages_rule_has_valid_glob_trigger(self):
        """kb-pages.md has trigger: glob with matching globs."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        path = rules_dir / "kb-pages.md"
        fm, body = parse_yaml_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual(fm.get("trigger"), "glob")
        self.assertTrue(fm.get("globs"))
        self.assertGreater(len(body), 200)

    def test_t3_23_rules_coincide_with_project_workflow(self):
        """Rules reference kb/ and work/ directories established in creative writing projects."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        for rule_path in rules_dir.glob("*.md"):
            content = rule_path.read_text(encoding="utf-8")
            self.assertTrue(
                "kb/" in content or "work/" in content,
                f"Rule {rule_path.name} does not reference kb/ or work/ workflow directories.",
            )

    def test_t3_24_rules_do_not_use_unknown_frontmatter_keys(self):
        """Rules frontmatters only contain valid Antigravity trigger keys."""
        valid_rule_keys = {"trigger", "description", "globs"}
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        for rule_path in rules_dir.glob("*.md"):
            fm, _ = parse_yaml_frontmatter(rule_path.read_text(encoding="utf-8"))
            unknown = set(fm.keys()) - valid_rule_keys
            self.assertEqual(
                unknown,
                set(),
                f"Rule {rule_path.name} contains invalid frontmatter keys: {unknown}",
            )

    def test_t3_25_rules_are_well_formed_markdown(self):
        """Rules start with YAML frontmatter markers and contain Markdown headings."""
        rules_dir = (
            TARGET_RULES_DIR if TARGET_RULES_DIR.exists() else OVERLAY_RULES_DIR
        )
        for rule_path in rules_dir.glob("*.md"):
            content = rule_path.read_text(encoding="utf-8")
            self.assertTrue(
                content.startswith("---\n"),
                f"Rule {rule_path.name} must start with frontmatter '---'",
            )
            self.assertIn(
                "\n# ",
                content,
                f"Rule {rule_path.name} must contain Markdown h1 header.",
            )


# ==============================================================================
# Tier 4: Real-World Application Scenarios (CLI Integration & Isolation)
# ==============================================================================
class Tier4RealWorldScenarioTests(unittest.TestCase):
    """End-to-end scenarios executing CLI commands, isolated installations, and workflows."""

    def test_t4_01_agy_plugin_validate_strict(self):
        """Execute `agy plugin validate <plugin> --strict --json` ensuring 0 errors and 0 warnings."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"Target plugin {TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        cmd = ["agy", "plugin", "validate", str(TARGET_PLUGIN_DIR), "--strict", "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(
            proc.returncode,
            0,
            f"`agy plugin validate --strict` failed with exit code {proc.returncode}:\nStdout: {proc.stdout}\nStderr: {proc.stderr}",
        )
        report = json.loads(proc.stdout)
        findings = report.get("findings", [])
        self.assertEqual(
            findings,
            [],
            f"`agy plugin validate --strict` emitted findings: {findings}",
        )

    def test_t4_02_agy_plugin_validate_component_counts(self):
        """Validate report confirms 15 agents and 28 skills discovered."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"Target plugin {TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        cmd = ["agy", "plugin", "validate", str(TARGET_PLUGIN_DIR), "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Validate failed: {proc.stderr}")
        report = json.loads(proc.stdout)
        components = report.get("components", {})
        self.assertEqual(
            components.get("agents"),
            15,
            f"Expected 15 agents in validate components, got {components.get('agents')}",
        )
        self.assertEqual(
            components.get("skills"),
            28,
            f"Expected 28 skills in validate components, got {components.get('skills')}",
        )

    def test_t4_03_isolated_home_plugin_install(self):
        """Install plugin into fresh isolated $HOME via `agy plugin install <target>`."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"Target plugin {TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            cmd = ["agy", "plugin", "install", str(TARGET_PLUGIN_DIR)]
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
            self.assertEqual(
                proc.returncode,
                0,
                f"`agy plugin install` failed in isolated HOME:\nStdout: {proc.stdout}\nStderr: {proc.stderr}",
            )
            self.assertIn("[ok]", proc.stdout)

    def test_t4_04_installed_directory_structure(self):
        """Verify installed plugin files exist at ~/.gemini/config/plugins/creative-writing-skills."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"{TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            subprocess.run(
                ["agy", "plugin", "install", str(TARGET_PLUGIN_DIR)],
                env=env,
                check=True,
                capture_output=True,
            )
            install_dir = (
                Path(tmp_home)
                / ".gemini"
                / "config"
                / "plugins"
                / "creative-writing-skills"
            )
            self.assertTrue(
                (install_dir / "plugin.json").is_file(),
                "plugin.json missing in installed plugin directory.",
            )
            self.assertTrue(
                (install_dir / "agents").is_dir(),
                "agents directory missing in installed plugin.",
            )
            self.assertTrue(
                (install_dir / "skills").is_dir(),
                "skills directory missing in installed plugin.",
            )
            self.assertTrue(
                (install_dir / "rules").is_dir(),
                "rules directory missing in installed plugin.",
            )

    def test_t4_05_import_manifest_registration(self):
        """Verify registration in ~/.gemini/config/import_manifest.json."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"{TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            subprocess.run(
                ["agy", "plugin", "install", str(TARGET_PLUGIN_DIR)],
                env=env,
                check=True,
                capture_output=True,
            )
            manifest_file = (
                Path(tmp_home) / ".gemini" / "config" / "import_manifest.json"
            )
            self.assertTrue(
                manifest_file.is_file(),
                "import_manifest.json missing after installation.",
            )
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            installed_plugins = set(data.get("plugins", {}).keys()) | {
                imp.get("name")
                for imp in data.get("imports", [])
                if isinstance(imp, dict) and "name" in imp
            }
            self.assertIn("creative-writing-skills", installed_plugins)

    def test_t4_06_agy_plugin_list_json_discovery(self):
        """Verify `agy plugin list --json` reflects installed plugin, version, and component counts."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"{TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            subprocess.run(
                ["agy", "plugin", "install", str(TARGET_PLUGIN_DIR)],
                env=env,
                check=True,
                capture_output=True,
            )
            proc = subprocess.run(
                ["agy", "plugin", "list", "--json"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"`agy plugin list` failed: {proc.stderr}")
            plugins = json.loads(proc.stdout)
            match = next(
                (p for p in plugins if p.get("name") == "creative-writing-skills"),
                None,
            )
            self.assertIsNotNone(match, "creative-writing-skills not found in plugin list.")
            self.assertEqual(match.get("version"), "0.7.4")
            self.assertTrue(match.get("enabled"))
            agents_val = match.get("agents")
            agents_count = len(agents_val) if isinstance(agents_val, list) else agents_val
            self.assertEqual(agents_count, 15)
            skills_val = match.get("skills")
            skills_count = len(skills_val) if isinstance(skills_val, list) else skills_val
            self.assertEqual(skills_count, 28)

    def test_t4_07_agy_agents_discovery(self):
        """Verify `agy agents` discovers declared entry agents (muse, writer, character-sim, outliner)."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"{TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            subprocess.run(
                ["agy", "plugin", "install", str(TARGET_PLUGIN_DIR)],
                env=env,
                check=True,
                capture_output=True,
            )
            proc = subprocess.run(
                ["agy", "agents"], env=env, capture_output=True, text=True
            )
            self.assertEqual(proc.returncode, 0, f"`agy agents` failed: {proc.stderr}")
            output = proc.stdout
            for expected_agent in ENTRY_AGENTS:
                self.assertIn(
                    expected_agent,
                    output,
                    f"Agent '{expected_agent}' not listed in `agy agents` output:\n{output}",
                )

    def test_t4_08_agy_plugin_disable_and_enable(self):
        """Verify plugin disable and enable lifecycle toggles activation state in CLI."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"{TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            subprocess.run(
                ["agy", "plugin", "install", str(TARGET_PLUGIN_DIR)],
                env=env,
                check=True,
                capture_output=True,
            )

            # Disable
            p_dis = subprocess.run(
                ["agy", "plugin", "disable", "creative-writing-skills"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(p_dis.returncode, 0)
            p_list1 = subprocess.run(
                ["agy", "plugin", "list", "--json"],
                env=env,
                capture_output=True,
                text=True,
            )
            plugins1 = json.loads(p_list1.stdout)
            match1 = next(
                p for p in plugins1 if p.get("name") == "creative-writing-skills"
            )
            self.assertFalse(match1.get("enabled"))

            # Enable
            p_en = subprocess.run(
                ["agy", "plugin", "enable", "creative-writing-skills"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(p_en.returncode, 0)
            p_list2 = subprocess.run(
                ["agy", "plugin", "list", "--json"],
                env=env,
                capture_output=True,
                text=True,
            )
            plugins2 = json.loads(p_list2.stdout)
            match2 = next(
                p for p in plugins2 if p.get("name") == "creative-writing-skills"
            )
            self.assertTrue(match2.get("enabled"))

    def test_t4_09_agy_plugin_uninstall(self):
        """Verify `agy plugin uninstall creative-writing-skills` removes the plugin cleanly."""
        if not TARGET_PLUGIN_DIR.exists():
            self.assertTrue(
                TARGET_PLUGIN_DIR.exists(),
                f"{TARGET_PLUGIN_DIR} does not exist yet (M3 pending).",
            )
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            subprocess.run(
                ["agy", "plugin", "install", str(TARGET_PLUGIN_DIR)],
                env=env,
                check=True,
                capture_output=True,
            )

            # Uninstall
            p_un = subprocess.run(
                ["agy", "plugin", "uninstall", "creative-writing-skills"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(p_un.returncode, 0)
            install_dir = (
                Path(tmp_home)
                / ".gemini"
                / "config"
                / "plugins"
                / "creative-writing-skills"
            )
            self.assertFalse(
                install_dir.exists(),
                "Plugin directory still exists after uninstallation.",
            )

    def test_t4_10_project_setup_workflow_guide(self):
        """Verify project setup workflow guide documents /project-setup and KB initial layout."""
        setup_guide = (
            TARGET_PLUGIN_DIR
            / "skills"
            / "project-setup"
            / "resources"
            / "antigravity.md"
            if TARGET_PLUGIN_DIR.exists()
            else OVERLAY_DIR
            / "skills"
            / "project-setup"
            / "resources"
            / "antigravity.md"
        )
        self.assertTrue(
            setup_guide.is_file(),
            f"Setup guide not found at {setup_guide}",
        )
        content = setup_guide.read_text(encoding="utf-8")
        self.assertIn("/project-setup", content)
        self.assertIn("kb/", content)
        self.assertIn("muse", content)

    def test_t4_11_native_dispatch_workflow_guide(self):
        """Verify native dispatch workflow guide documents invoke_subagent and multi-agent roles."""
        dispatch_guide = (
            TARGET_PLUGIN_DIR
            / "skills"
            / "writing-staffing"
            / "resources"
            / "antigravity-dispatch.md"
            if TARGET_PLUGIN_DIR.exists()
            else OVERLAY_DIR
            / "skills"
            / "writing-staffing"
            / "resources"
            / "antigravity-dispatch.md"
        )
        self.assertTrue(
            dispatch_guide.is_file(),
            f"Dispatch guide not found at {dispatch_guide}",
        )
        content = dispatch_guide.read_text(encoding="utf-8")
        self.assertIn("invoke_subagent", content)
        self.assertIn("critic", content)
        self.assertIn("writer", content)
        self.assertIn("kb-lead", content)


# ==============================================================================
# Main Runner & CLI Execution
# ==============================================================================
def run_suite(verbosity: int = 2) -> unittest.TestResult:
    """Run all 4 tiers of the test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(Tier1FeatureCoverageTests))
    suite.addTests(loader.loadTestsFromTestCase(Tier2BoundaryCornerCaseTests))
    suite.addTests(loader.loadTestsFromTestCase(Tier3CrossFeatureCombinationTests))
    suite.addTests(loader.loadTestsFromTestCase(Tier4RealWorldScenarioTests))

    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


if __name__ == "__main__":
    result = run_suite()
    sys.exit(0 if result.wasSuccessful() else 1)
