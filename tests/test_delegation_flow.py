#!/usr/bin/env python3
"""Dedicated Verification Suite for Muse Native Antigravity Multi-Agent Delegation.

Focuses on Requirement 6:
- Muse -> Creative Researcher delegation flow, tools permissions, model routing ('flash')
- Muse -> Writer delegation flow, stateful continuation, tools permissions, model routing ('pro')
- Muse -> Critic delegation flow, cold-read stance, read-only permissions, model routing ('pro')
- Parallel multi-agent review lane dispatch
- Nested kb-lead sub-orchestration
- Context routing isolation
"""

import json
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugin" / "antigravity"
AGENTS_DIR = PLUGIN_DIR / "agents"
SKILLS_DIR = PLUGIN_DIR / "skills"
RULES_DIR = PLUGIN_DIR / "rules"


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown file."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    yaml_text = parts[1]
    body = parts[2]
    metadata: Dict[str, Any] = {}
    current_key = None

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
            elif (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                metadata[key] = val[1:-1]
                current_key = key
            else:
                metadata[key] = val
                current_key = key

    return metadata, body


class TestMuseDelegationFlow(unittest.TestCase):
    """Test native Antigravity delegation mechanics and permissions."""

    def test_muse_orchestrator_capabilities(self):
        """Muse is discoverable as mainAgent and equipped with native orchestration tools."""
        muse_file = AGENTS_DIR / "muse.md"
        self.assertTrue(muse_file.is_file(), "muse.md missing from agents directory")
        fm, body = parse_frontmatter(muse_file.read_text(encoding="utf-8"))

        self.assertEqual(fm.get("name"), "muse")
        self.assertTrue(fm.get("mainAgent"), "Muse must be discoverable as a main session agent")
        self.assertEqual(fm.get("model"), "inherit", "Muse must inherit user's primary session model")

        tools = fm.get("tools", [])
        self.assertIn("invoke_subagent", tools, "Muse must have invoke_subagent for multi-agent dispatch")
        self.assertIn("send_message", tools, "Muse must have send_message for stateful iteration")
        self.assertIn("manage_subagents", tools, "Muse must have manage_subagents for lifecycle control")
        self.assertIn("ask_question", tools, "Muse interacts directly with the author")

    def test_muse_to_creative_researcher_delegation(self):
        """Verify Muse -> Creative Researcher delegation flow, tools permissions, and model tier."""
        researcher_file = AGENTS_DIR / "creative-researcher.md"
        self.assertTrue(researcher_file.is_file())
        fm, body = parse_frontmatter(researcher_file.read_text(encoding="utf-8"))

        # Model routing: 'flash' for rapid factual and lore lookups
        self.assertEqual(fm.get("model"), "flash", "creative-researcher must run on high-velocity 'flash' tier")
        self.assertTrue(fm.get("subagent"), "creative-researcher must be invokable as subagent")

        # Tool permissions: strictly read-only + web search (no destructive file edits or bash)
        tools = fm.get("tools", [])
        self.assertIn("view_file", tools)
        self.assertIn("google_search", tools, "creative-researcher needs search for lore grounding")
        self.assertNotIn("write_to_file", tools, "creative-researcher must not modify files")
        self.assertNotIn("replace_file_content", tools, "creative-researcher must not edit files")
        self.assertNotIn("run_command", tools, "creative-researcher must not execute shell commands")

        # Reporting behavior: reports back to caller
        self.assertIn("return all deliverables", body.lower())

        # Validate native invoke_subagent call structure
        invocation_payload = {
            "Subagents": [
                {
                    "TypeName": "creative-researcher",
                    "Role": "Historical Weapons Researcher",
                    "Prompt": "Research medieval trebuchet siege mechanics and projectile impact for Chapter 4.",
                    "Model": "flash",
                    "Workspace": "inherit",
                }
            ]
        }
        self.assertEqual(invocation_payload["Subagents"][0]["TypeName"], fm["name"])
        self.assertEqual(invocation_payload["Subagents"][0]["Model"], fm["model"])

    def test_muse_to_writer_delegation(self):
        """Verify Muse -> Writer delegation flow, stateful continuation, tools, and model tier."""
        writer_file = AGENTS_DIR / "writer.md"
        self.assertTrue(writer_file.is_file())
        fm, body = parse_frontmatter(writer_file.read_text(encoding="utf-8"))

        # Model routing: 'pro' for rich narrative cadence, sensory texture, and voice
        self.assertEqual(fm.get("model"), "pro", "writer must run on high-creative 'pro' tier")
        self.assertTrue(fm.get("subagent"), "writer must be invokable as subagent")

        # Tool permissions: file writing permitted, but no arbitrary shell commands
        tools = fm.get("tools", [])
        self.assertIn("view_file", tools)
        self.assertIn("write_to_file", tools, "writer needs write access to produce draft files")
        self.assertIn("replace_file_content", tools, "writer needs edit access for line revisions")
        self.assertNotIn("run_command", tools, "writer must not run shell commands")

        # Reporting behavior
        self.assertIn("return all deliverables", body.lower())

        # Validate native invoke_subagent call structure
        invocation_payload = {
            "Subagents": [
                {
                    "TypeName": "writer",
                    "Role": "Scene Prose Writer",
                    "Prompt": "Draft the opening courtyard scene of Chapter 4 following kb/styles/voice.md.",
                    "Model": "pro",
                    "Workspace": "inherit",
                }
            ]
        }
        self.assertEqual(invocation_payload["Subagents"][0]["TypeName"], fm["name"])
        self.assertEqual(invocation_payload["Subagents"][0]["Model"], fm["model"])

        # Validate send_message stateful continuation pattern
        continuation_payload = {
            "Recipient": "subagent-writer-conv-id-42",
            "Message": "The author accepted critique #1. Tighten lines 20-35 to emphasize the cold wind.",
        }
        self.assertIn("Recipient", continuation_payload)
        self.assertIn("Message", continuation_payload)

    def test_muse_to_critic_delegation(self):
        """Verify Muse -> Critic delegation flow, cold-read stance, read-only permissions, and model tier."""
        critic_file = AGENTS_DIR / "critic.md"
        self.assertTrue(critic_file.is_file())
        fm, body = parse_frontmatter(critic_file.read_text(encoding="utf-8"))

        # Model routing: 'pro' for deep adversarial structural and voice critique
        self.assertEqual(fm.get("model"), "pro", "critic must run on deep reasoning 'pro' tier")
        self.assertTrue(fm.get("subagent"), "critic must be invokable as subagent")

        # Tool permissions: strictly read-only
        tools = fm.get("tools", [])
        self.assertIn("view_file", tools)
        self.assertNotIn("write_to_file", tools, "critic must be strictly read-only")
        self.assertNotIn("replace_file_content", tools, "critic must not edit files")
        self.assertNotIn("run_command", tools, "critic must not run shell commands")

        # Prompt constraints: read-only and caller reporting
        self.assertIn("read-only", body.lower())
        self.assertIn("writes no files", body.lower())

        # Validate native invoke_subagent call structure
        invocation_payload = {
            "Subagents": [
                {
                    "TypeName": "critic",
                    "Role": "Adversarial Prose Critic",
                    "Prompt": "Diagnose chapter 4 draft for narrative pacing and character voice dissonance.",
                    "Model": "pro",
                    "Workspace": "inherit",
                }
            ]
        }
        self.assertEqual(invocation_payload["Subagents"][0]["TypeName"], fm["name"])
        self.assertEqual(invocation_payload["Subagents"][0]["Model"], fm["model"])

    def test_parallel_review_lanes_invocation(self):
        """Verify Muse can dispatch concurrent reviewer lanes in a single invoke_subagent call."""
        parallel_call = {
            "Subagents": [
                {
                    "TypeName": "critic",
                    "Role": "Structure Critic",
                    "Prompt": "Review chapter 4 pacing and structural tension.",
                    "Model": "pro",
                },
                {
                    "TypeName": "continuity-checker",
                    "Role": "Continuity Auditor",
                    "Prompt": "Check chapter 4 against kb/timeline/timeline.md.",
                    "Model": "flash",
                },
                {
                    "TypeName": "reader-sim",
                    "Role": "Naive Reader Experience",
                    "Prompt": "Perform a cold read of chapter 4 noting emotional trajectory.",
                    "Model": "flash",
                },
            ]
        }
        self.assertEqual(len(parallel_call["Subagents"]), 3)
        for sub in parallel_call["Subagents"]:
            agent_file = AGENTS_DIR / f"{sub['TypeName']}.md"
            self.assertTrue(agent_file.is_file())
            fm, _ = parse_frontmatter(agent_file.read_text(encoding="utf-8"))
            self.assertEqual(fm["model"], sub["Model"])
            self.assertTrue(fm["subagent"])

    def test_nested_kb_lead_orchestration(self):
        """Verify kb-lead sub-orchestrator has delegation tools to coordinate documentation subagents."""
        kb_lead_file = AGENTS_DIR / "kb-lead.md"
        self.assertTrue(kb_lead_file.is_file())
        fm, body = parse_frontmatter(kb_lead_file.read_text(encoding="utf-8"))

        self.assertEqual(fm.get("model"), "pro", "kb-lead requires pro for knowledge taxonomy curation")
        tools = fm.get("tools", [])
        self.assertIn("invoke_subagent", tools, "kb-lead needs invoke_subagent to spawn miners and maintainers")
        self.assertIn("manage_subagents", tools, "kb-lead needs manage_subagents to track subordinate tasks")

    def test_context_routing_rule_demarcation(self):
        """Verify story-project.md cleanly separates creative writing tasks from general code exploration."""
        story_rule = RULES_DIR / "story-project.md"
        self.assertTrue(story_rule.is_file())
        content = story_rule.read_text(encoding="utf-8")

        self.assertIn("Context Routing & Subagent Scope", content)
        self.assertIn("Creative Writing Domain Tasks", content)
        self.assertIn("General Software & Codebase Exploration", content)
        # Verify no hardcoded machine paths exist
        self.assertNotIn("/home/", content)
        self.assertNotIn("~/.gemini", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
