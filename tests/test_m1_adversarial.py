#!/usr/bin/env python3
"""Adversarial stress test harness for Milestone 1 deliverables.

Tests:
1. TOML parsing on corrupted/malformed variants vs genuine files.
2. Hash mismatch detection on `patches.toml` if upstream is perturbed.
3. Patch search string uniqueness in upstream files (count == 1).
4. Strict JSON parsing on `plugin.json.tmpl` (RFC 8259 rejection of comments, trailing commas).
5. User model directive conformance and agent frontmatter schema.
6. Rules size and frontmatter bounds.
7. git_guard.py hook execution across benign, destructive, and adversarial inputs.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from typing import Any
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ANTIGRAVITY_DIR = REPO_ROOT / "antigravity"
AGENTS_TOML = ANTIGRAVITY_DIR / "agents.toml"
PATCHES_TOML = ANTIGRAVITY_DIR / "patches.toml"
OVERLAY_DIR = ANTIGRAVITY_DIR / "overlay"
PLUGIN_JSON_TMPL = OVERLAY_DIR / "plugin.json.tmpl"
GIT_GUARD = OVERLAY_DIR / "scripts" / "git_guard.py"
HOOKS_JSON = OVERLAY_DIR / "hooks.json"
RULES_DIR = OVERLAY_DIR / "rules"
UPSTREAM_CLAUDE_DIR = REPO_ROOT / "plugin" / "claude"


class TestAdversarialTomlParsing(unittest.TestCase):
    """Stress-test TOML parsing with valid and corrupted/malformed variants."""

    def test_genuine_agents_toml_parses(self):
        self.assertTrue(AGENTS_TOML.exists(), f"{AGENTS_TOML} does not exist.")
        with open(AGENTS_TOML, "rb") as f:
            data = tomllib.load(f)
        self.assertIn("defaults", data)
        self.assertIn("agents", data)
        self.assertEqual(len(data["agents"]), 15)

    def test_genuine_patches_toml_parses(self):
        self.assertTrue(PATCHES_TOML.exists(), f"{PATCHES_TOML} does not exist.")
        with open(PATCHES_TOML, "rb") as f:
            data = tomllib.load(f)
        self.assertIn("patches", data)
        self.assertEqual(len(data["patches"]), 6)

    def test_agents_toml_malformed_syntax_corruptions(self):
        raw_bytes = AGENTS_TOML.read_bytes()
        raw_text = raw_bytes.decode("utf-8")

        corruptions = [
            ("unclosed_double_quote", raw_text.replace('model = "inherit"', 'model = "inherit')),
            ("unclosed_single_quote", raw_text.replace('model = "inherit"', "model = 'inherit")),
            ("missing_closing_bracket", raw_text.replace("[agents.muse]", "[agents.muse")),
            ("missing_opening_bracket", raw_text.replace("[agents.muse]", "agents.muse]")),
            ("double_equals", raw_text.replace('model = "inherit"', 'model = = "inherit"')),
            ("duplicate_key_in_table", raw_text.replace('model = "inherit"', 'model = "inherit"\nmodel = "flash"')),
            ("unterminated_array", raw_text.replace('skills = [\n  "skills/creative-writing-muse",', 'skills = [\n  "skills/creative-writing-muse"')),
            ("bare_non_boolean_word", raw_text.replace('mainAgent = true', 'mainAgent = true_maybe')),
            ("invalid_bare_key", raw_text.replace('subagent = false', 'subagent @#$ = false')),
        ]

        for name, corrupt_text in corruptions:
            with self.subTest(corruption=name):
                with self.assertRaises(tomllib.TOMLDecodeError, msg=f"Corruption {name} should raise TOMLDecodeError"):
                    tomllib.loads(corrupt_text)

    def test_patches_toml_malformed_syntax_corruptions(self):
        raw_text = PATCHES_TOML.read_text(encoding="utf-8")

        corruptions = [
            ("unclosed_multiline_string", raw_text.replace('"""## First, Load One Environment Walkthrough', '""## First, Load One Environment Walkthrough')),
            ("unterminated_multiline_triple_quote", raw_text.replace('use the environment you are\nin."""', 'use the environment you are\nin.""')),
            ("duplicate_section_header", raw_text.replace('[[patches]]', '[[patches]]\n[[patches]]\nfile = "skills/project-setup/SKILL.md"\nfile = "dupe"')),
            ("invalid_key_assignment", raw_text.replace('sha256 = "', 'sha256 : "')),
        ]

        for name, corrupt_text in corruptions:
            with self.subTest(corruption=name):
                with self.assertRaises(tomllib.TOMLDecodeError, msg=f"Corruption {name} should raise TOMLDecodeError"):
                    tomllib.loads(corrupt_text)

    def test_truncated_toml_variants(self):
        for toml_path in [AGENTS_TOML, PATCHES_TOML]:
            content = toml_path.read_text(encoding="utf-8")
            cutoffs = [0.1, 0.25, 0.5, 0.75, 0.95]
            for frac in cutoffs:
                cutoff_idx = int(len(content) * frac)
                # Find a newline boundary or slice directly
                sliced = content[:cutoff_idx]
                try:
                    tomllib.loads(sliced)
                except tomllib.TOMLDecodeError:
                    pass  # Expected for almost all cuts
                except Exception as e:
                    self.fail(f"Truncation of {toml_path.name} at {frac:.2f} threw unexpected exception: {e}")


class TestAdversarialPatchHashMismatch(unittest.TestCase):
    """Stress-test SHA-256 hash gating and perturbation detection in patches.toml."""

    def setUp(self):
        with open(PATCHES_TOML, "rb") as f:
            self.patches_data = tomllib.load(f)["patches"]

    def test_all_upstream_files_exist_and_hashes_match(self):
        self.assertEqual(len(self.patches_data), 6)
        for p in self.patches_data:
            target = UPSTREAM_CLAUDE_DIR / p["file"]
            self.assertTrue(target.exists(), f"Target file does not exist: {target}")
            actual_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertEqual(
                actual_hash,
                p["sha256"],
                f"SHA-256 mismatch for {p['file']}: expected {p['sha256']}, got {actual_hash}"
            )

    def test_perturbation_detection_single_byte_flip(self):
        """Ensure any single byte modification in upstream breaks the SHA-256 gate."""
        for p in self.patches_data:
            target = UPSTREAM_CLAUDE_DIR / p["file"]
            original_bytes = target.read_bytes()

            # Flip first byte
            perturbed_bytes = bytes([(original_bytes[0] ^ 0xFF)]) + original_bytes[1:]
            perturbed_hash = hashlib.sha256(perturbed_bytes).hexdigest()
            self.assertNotEqual(
                perturbed_hash,
                p["sha256"],
                f"Byte flip on {p['file']} did not alter SHA-256! (Impossible hash collision)"
            )

    def test_perturbation_detection_whitespace_and_newlines(self):
        """Ensure trailing newline or subtle whitespace changes alter the hash."""
        for p in self.patches_data:
            target = UPSTREAM_CLAUDE_DIR / p["file"]
            original_bytes = target.read_bytes()

            # Append newline
            appended = original_bytes + b"\n"
            self.assertNotEqual(hashlib.sha256(appended).hexdigest(), p["sha256"])

            # Prepend space
            prepended = b" " + original_bytes
            self.assertNotEqual(hashlib.sha256(prepended).hexdigest(), p["sha256"])

            # Windows CRLF perturbation
            crlf_version = original_bytes.replace(b"\n", b"\r\n")
            if crlf_version != original_bytes:
                self.assertNotEqual(hashlib.sha256(crlf_version).hexdigest(), p["sha256"])

    def test_simulated_gated_patch_applicator_rejects_perturbed_upstream(self):
        """Simulate build_antigravity patch step: must abort if hash mismatches."""
        for p in self.patches_data:
            target = UPSTREAM_CLAUDE_DIR / p["file"]
            original_content = target.read_text(encoding="utf-8")
            # Perturb content
            perturbed_content = original_content + "\n# unexpected edit"
            perturbed_hash = hashlib.sha256(perturbed_content.encode("utf-8")).hexdigest()

            def apply_patch(content, expected_hash, search, replace):
                actual_h = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if actual_h != expected_hash:
                    raise ValueError(f"Upstream file hash mismatch! Expected {expected_hash}, got {actual_h}")
                if search not in content:
                    raise KeyError("Search string not found")
                return content.replace(search, replace, 1)

            # Assert rejection on perturbed
            with self.assertRaises(ValueError):
                apply_patch(perturbed_content, p["sha256"], p["search"], p["replace"])

            # Assert success on genuine
            result = apply_patch(original_content, p["sha256"], p["search"], p["replace"])
            self.assertIn(p["replace"], result)
            self.assertNotIn(p["search"], result)


class TestAdversarialPatchSearchUniqueness(unittest.TestCase):
    """Stress-test patch search strings to ensure EXACTLY ONE occurrence in target file."""

    def setUp(self):
        with open(PATCHES_TOML, "rb") as f:
            self.patches_data = tomllib.load(f)["patches"]

    def test_search_string_uniqueness_exact_count_is_one(self):
        """Verify each search string appears exactly 1 time in the upstream file (no ambiguity)."""
        for i, p in enumerate(self.patches_data):
            target = UPSTREAM_CLAUDE_DIR / p["file"]
            content = target.read_text(encoding="utf-8")
            count = content.count(p["search"])
            self.assertEqual(
                count,
                1,
                f"Patch #{i+1} on {p['file']}: search string must appear EXACTLY ONCE, but found {count} occurrences!"
            )

    def test_no_forbidden_claude_artifacts_in_replacement_strings(self):
        """Ensure replacements do not reintroduce Claude/Meridian models or tools."""
        forbidden_terms = [
            "opus",
            "sonnet",
            "meridian spawn",
            "meridian mars",
            "/creative-writing-skills:",
            "AskUserQuestion",
            "NotebookEdit",
        ]
        for p in self.patches_data:
            replace_str = p["replace"]
            for term in forbidden_terms:
                self.assertNotIn(
                    term,
                    replace_str,
                    f"Replacement for {p['file']} contains forbidden Claude artifact '{term}'"
                )

    def test_referenced_overlay_resources_exist(self):
        """If a replacement references an overlay resource, verify the resource actually exists."""
        # Patch 1 references resources/antigravity.md
        p1_res = OVERLAY_DIR / "skills" / "project-setup" / "resources" / "antigravity.md"
        self.assertTrue(p1_res.exists(), f"Patch 1 references {p1_res} which does not exist")

        # Patch 2 references resources/antigravity-dispatch.md
        p2_res = OVERLAY_DIR / "skills" / "writing-staffing" / "resources" / "antigravity-dispatch.md"
        self.assertTrue(p2_res.exists(), f"Patch 2 references {p2_res} which does not exist")


class TestAdversarialJsonStrictness(unittest.TestCase):
    """Stress-test strict RFC 8259 JSON parsing on plugin.json.tmpl."""

    def test_genuine_template_is_valid_rfc8259_json(self):
        self.assertTrue(PLUGIN_JSON_TMPL.exists())
        raw_text = PLUGIN_JSON_TMPL.read_text(encoding="utf-8")
        parsed = json.loads(raw_text)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["name"], "creative-writing-skills")
        with open(REPO_ROOT / "mars.toml", "rb") as source:
            expected_version = tomllib.load(source)["package"]["version"]
        self.assertEqual(parsed["version"], expected_version)

    def test_strict_rejection_of_comments(self):
        """Standard JSON parsers must reject single-line and multi-line comments."""
        raw_text = PLUGIN_JSON_TMPL.read_text(encoding="utf-8")

        comment_variants = [
            ("// leading comment\n" + raw_text),
            (raw_text.replace('"$schema"', '// schema link\n  "$schema"')),
            (raw_text.replace('"name": "creative-writing-skills"', '"name": "creative-writing-skills" // plugin name')),
            ("/* block comment */\n" + raw_text),
            (raw_text.replace('"keywords": [', '"keywords": /* keywords */ [')),
            (raw_text + "\n// trailing comment"),
        ]

        for i, variant in enumerate(comment_variants):
            with self.subTest(comment_variant=i):
                with self.assertRaises(json.JSONDecodeError, msg=f"Comment variant {i} should fail strict json.loads"):
                    json.loads(variant)

    def test_strict_rejection_of_trailing_commas(self):
        """Standard JSON parsers must reject trailing commas in objects and arrays."""
        raw_text = PLUGIN_JSON_TMPL.read_text(encoding="utf-8")

        trailing_variants = [
            # Trailing comma in array
            raw_text.replace('"Review this draft for character voice and narrative pacing"', '"Review this draft for character voice and narrative pacing",'),
            # Trailing comma in object
            raw_text.replace('"Review this draft for character voice and narrative pacing"\n  ]', '"Review this draft for character voice and narrative pacing"\n  ],\n'),
            # Trailing comma in nested author object
            raw_text.replace('"email": "dev.jimm.py@gmail.com"', '"email": "dev.jimm.py@gmail.com",'),
            # Trailing comma in keywords array
            raw_text.replace('"muse"\n  ]', '"muse",\n  ]'),
        ]

        for i, variant in enumerate(trailing_variants):
            with self.subTest(trailing_comma_variant=i):
                with self.assertRaises(json.JSONDecodeError, msg=f"Trailing comma variant {i} should fail strict json.loads"):
                    json.loads(variant)

    def test_strict_rejection_of_unquoted_and_single_quoted_keys(self):
        raw_text = PLUGIN_JSON_TMPL.read_text(encoding="utf-8")

        unquoted = raw_text.replace('"name": "creative-writing-skills"', 'name: "creative-writing-skills"')
        with self.assertRaises(json.JSONDecodeError):
            json.loads(unquoted)

        single_quoted = raw_text.replace('"name": "creative-writing-skills"', "'name': 'creative-writing-skills'")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(single_quoted)

    def test_schema_conformance(self):
        raw_text = PLUGIN_JSON_TMPL.read_text(encoding="utf-8")
        data = json.loads(raw_text)

        # Name must be strict kebab-case
        self.assertRegex(data["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")

        # Version must be valid semver
        self.assertRegex(data["version"], r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")

        # Suggested prompts bounds (1 to 3 prompts permitted in Antigravity)
        prompts = data.get("suggestedPrompts", [])
        self.assertGreaterEqual(len(prompts), 1)
        self.assertLessEqual(len(prompts), 3, "Antigravity plugin schema allows maximum 3 suggestedPrompts")

        # Logo path
        logo_path = data.get("logo", "")
        self.assertTrue(logo_path.endswith(".svg"), f"Logo should be SVG: {logo_path}")
        self.assertTrue((OVERLAY_DIR / logo_path).exists(), f"Logo file does not exist at {OVERLAY_DIR / logo_path}")


class TestAdversarialModelAndAgentsConfig(unittest.TestCase):
    """Stress-test user binding model directive and agent topology."""

    def setUp(self):
        with open(AGENTS_TOML, "rb") as f:
            self.config = tomllib.load(f)

    def test_muse_model_is_strictly_inherit(self):
        muse = self.config["agents"]["muse"]
        self.assertEqual(
            muse.get("model"),
            "inherit",
            f"User directive violation: muse model must be 'inherit', found '{muse.get('model')}'"
        )

    def test_subagents_follow_role_model_policy(self):
        """Creative judgment roles inherit; the nine other specialists use flash."""
        agents = self.config["agents"]
        for name, cfg in agents.items():
            if name == "muse":
                continue
            model = cfg.get("model", self.config.get("defaults", {}).get("model"))
            inherited = {"writer", "critic", "outliner", "style-creator", "kb-lead"}
            expected = "inherit" if name in inherited else "flash"
            self.assertEqual(
                model,
                expected,
                f"Model policy violation: agent '{name}' must use '{expected}', found '{model}'"
            )

    def test_agent_tools_allowlists(self):
        """Verify all agents define official tools allowlists with least privilege enforcement."""
        reviewers = {"critic", "character-sim", "continuity-checker", "reader-sim", "explorer", "session-miner", "cold-reader"}
        agents = self.config["agents"]
        for name, cfg in agents.items():
            tools = cfg.get("tools", [])
            self.assertIsInstance(tools, list, f"Agent '{name}' tools must be a list")
            self.assertGreater(len(tools), 0, f"Agent '{name}' tools list must not be empty")
            self.assertNotIn("google_search", tools, f"Agent '{name}' uses unofficial 'google_search'; must use 'search_web'")
            if name in reviewers:
                for forbidden in ("write_to_file", "replace_file_content", "multi_replace_file_content", "run_command"):
                    self.assertNotIn(forbidden, tools, f"Reviewer agent '{name}' cannot have edit/run tool '{forbidden}'")



    def test_main_agent_flags(self):
        """Only muse, writer, character-sim, outliner may have mainAgent: true."""
        expected_main = {"muse", "writer", "character-sim", "outliner"}
        for name, cfg in self.config["agents"].items():
            is_main = cfg.get("mainAgent", False)
            if name in expected_main:
                self.assertTrue(is_main, f"Expected {name} to have mainAgent=True")
            else:
                self.assertFalse(is_main, f"Expected {name} to have mainAgent=False")

    def test_subagent_flags(self):
        """Muse must have subagent=False, all other 14 must have subagent=True."""
        for name, cfg in self.config["agents"].items():
            is_sub = cfg.get("subagent", True)
            if name == "muse":
                self.assertFalse(is_sub, "muse must have subagent=False")
            else:
                self.assertTrue(is_sub, f"agent {name} must have subagent=True")

    def test_command_execution_policy(self):
        defaults = self.config.get("defaults", {})
        self.assertEqual(
            defaults.get("commandExecutionPolicy"),
            "sandbox",
            "Default commandExecutionPolicy must be 'sandbox'"
        )

    def test_closure_referential_integrity(self):
        """Every referenced skill in agents.toml must exist in plugin/claude/skills/."""
        available_skills = {d.name for d in UPSTREAM_CLAUDE_DIR.glob("skills/*") if d.is_dir()}
        for agent_name, cfg in self.config["agents"].items():
            for skill_ref in cfg.get("skills", []):
                skill_stem = skill_ref.split("/")[-1]
                self.assertIn(
                    skill_stem,
                    available_skills,
                    f"Agent '{agent_name}' references non-existent skill '{skill_ref}'"
                )
            for skill_ref in cfg.get("optional_skills", []):
                skill_stem = skill_ref.split("/")[-1]
                self.assertIn(
                    skill_stem,
                    available_skills,
                    f"Agent '{agent_name}' references non-existent optional skill '{skill_ref}'"
                )

    def test_muse_subagents_list_coverage(self):
        """Muse declares subagents it orchestrates. Check coverage of subagents."""
        declared = set(self.config["agents"]["muse"].get("subagents", []))
        all_other_agents = set(self.config["agents"].keys()) - {"muse"}
        missing = all_other_agents - declared
        self.assertIn("writer", declared)
        self.assertIn("critic", declared)
        self.assertIn("reader-sim", declared)
        self.assertIn("kb-lead", declared)
        # Muse declares all 14 subagents so missing is empty
        self.assertEqual(missing, set(), f"Unexpected omission from muse.subagents: {missing}")


class TestAdversarialGitGuardHook(unittest.TestCase):
    """Stress-test git_guard hook with varied normal, destructive, and adversarial inputs."""

    def run_hook(self, payload: Any) -> dict:
        if isinstance(payload, str):
            input_data = payload
        else:
            input_data = json.dumps(payload)

        proc = subprocess.run(
            [str(GIT_GUARD)],
            input=input_data,
            text=True,
            capture_output=True,
            check=False
        )
        self.assertEqual(proc.returncode, 0, f"git_guard returned non-zero code {proc.returncode}: {proc.stderr}")
        return json.loads(proc.stdout)

    def test_destructive_commands_trigger_ask(self):
        destructive = [
            "git reset --hard",
            "git reset --hard HEAD",
            "git reset --hard HEAD~1",
            "git reset origin/main --hard",
            "git clean -fd",
            "git clean -f",
            "git clean -xdf",
            "git restore .",
            "git restore --staged file.txt",
            "git checkout -- file.py",
            "git checkout path/to/file -- file.py",
            "git revert HEAD",
            "git revert abc1234",
            "git   reset   --hard   HEAD",  # Multiple spaces
            "cd dir && git reset --hard HEAD",  # Chained command
            "echo 'yes' | git clean -fd",  # Piped command
        ]

        for cmd in destructive:
            with self.subTest(cmd=cmd):
                res = self.run_hook({"toolCall": {"args": {"CommandLine": cmd}}})
                self.assertEqual(res.get("decision"), "ask", f"Command '{cmd}' should return 'ask', got '{res}'")
                self.assertIn("reason", res)

    def test_benign_commands_trigger_allow(self):
        benign = [
            "git status",
            "git status --short",
            "git diff",
            "git diff HEAD~1",
            "git log -n 5",
            "git checkout main",
            "git checkout -b feature",
            "git branch -a",
            "git commit -m 'feat: update'",
            "ls -la",
            "python3 -m unittest",
            "git reset HEAD~1",  # Soft/mixed reset is not --hard
        ]

        for cmd in benign:
            with self.subTest(cmd=cmd):
                res = self.run_hook({"toolCall": {"args": {"CommandLine": cmd}}})
                self.assertEqual(res.get("decision"), "allow", f"Command '{cmd}' should return 'allow', got '{res}'")

    def test_adversarial_malformed_inputs_handled(self):
        """git_guard safely handles syntax errors, whitespace, and alternate keys."""
        safe_inputs = [
            "",  # Empty stdin
            "   \n\t  ",  # Whitespace only
            "{invalid json",  # Syntax error
            "{}",  # Empty object
            json.dumps({"toolCall": {}}),
            json.dumps({"toolCall": {"args": {}}}),
            json.dumps({"toolCall": {"args": {"CommandLine": ""}}}),
            json.dumps({"toolCall": {"args": {"cmd": "git reset --hard"}}}),  # Alternate key
            json.dumps({"CommandLine": "git reset --hard"}),  # Top-level key
        ]

        for payload in safe_inputs:
            with self.subTest(payload=repr(payload)):
                res = self.run_hook(payload)
                self.assertIn(res.get("decision"), ["allow", "ask"])

    def test_vulnerability_git_guard_crashes_on_non_dict_or_null_toolcall(self):
        """Verify that git_guard.py handles non-dict JSON or null toolCall safely
        with exit code 0, conforming to the fail-open contract.
        """
        failing_inputs = [
            "12345",  # Number JSON
            "\"string value\"",  # Plain string JSON
            "[]",  # Array JSON
            json.dumps({"toolCall": None}),  # Null toolCall
        ]

        for payload in failing_inputs:
            with self.subTest(payload=repr(payload)):
                proc = subprocess.run(
                    [str(GIT_GUARD)],
                    input=payload,
                    text=True,
                    capture_output=True,
                    check=False
                )
                # Confirm safe handling (fail-open) with exit code 0
                self.assertEqual(
                    proc.returncode,
                    0,
                    f"Expected exit code 0 on {payload}, got {proc.returncode}"
                )


class TestAdversarialRulesAndDocsBounds(unittest.TestCase):
    """Stress-test rules file sizes, triggers, and content limits."""

    def test_rule_file_sizes_under_24kb(self):
        max_bytes = 24000
        for rule_file in RULES_DIR.glob("*.md"):
            size = rule_file.stat().st_size
            self.assertLessEqual(
                size,
                max_bytes,
                f"Rule file {rule_file.name} exceeds 24KB limit ({size} bytes)"
            )

    def test_rule_frontmatters(self):
        story_rule = (RULES_DIR / "story-project.md").read_text(encoding="utf-8")
        self.assertTrue(story_rule.startswith("---\n"))
        self.assertIn("trigger: model_decision", story_rule)
        self.assertIn("description:", story_rule)

        kb_rule = (RULES_DIR / "kb-pages.md").read_text(encoding="utf-8")
        self.assertTrue(kb_rule.startswith("---\n"))
        self.assertIn("trigger: glob", kb_rule)
        self.assertIn("globs:", kb_rule)


if __name__ == "__main__":
    unittest.main(verbosity=2)
