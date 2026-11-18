#!/usr/bin/env python3
"""Build or verify the installed Codex reading copy from the checked-in Mars inputs/output."""
import argparse
import json
import subprocess
from tempfile import TemporaryDirectory
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "plugins/creative-writing-skills/reference"
CLAUDE = ROOT / "plugin/claude"


def sources(base_repo, revision):
    # Keep the native model policies and original skill bodies wherever available.
    for role in sorted((CLAUDE / "agents").glob("*.md")):
        native = ROOT / "agents" / role.name
        if native.is_file():
            data = native.read_bytes()
        else:
            data = subprocess.check_output(
                ["git", "-C", base_repo, "show", f"{revision}^{{commit}}:agents/{role.name}"]
            )
        yield Path("agents") / role.name, data
        yield Path("claude-agents") / role.name, role.read_bytes()
    for compiled in sorted((CLAUDE / "skills").iterdir()):
        # Destination sync is a separate CLI-bearing dependency, not a writing lane.
        if not compiled.is_dir() or compiled.name == "writing-sync":
            continue
        source = ROOT / "skills" / compiled.name
        if not source.is_dir():
            source = compiled
        for item in sorted(source.rglob("*")):
            if item.is_file():
                yield Path("skills") / compiled.name / item.relative_to(source), item.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report stale output without writing")
    parser.add_argument("--meridian-base", type=Path, help="existing Git checkout with the pinned revision")
    args = parser.parse_args()
    lock = json.loads((ROOT / "plugin/.mars-plugin.json").read_text())["dependencies"]["meridian-base"]
    with TemporaryDirectory() as temp:
        base_repo = args.meridian_base
        if base_repo is None:
            base_repo = Path(temp) / "meridian-base"
            subprocess.run(
                ["git", "clone", "--quiet", "--no-checkout", "--depth", "1", "--branch",
                 f"v{lock['version']}", "https://github.com/haowjy/meridian-base.git", base_repo],
                check=True,
            )
        expected = dict(sources(base_repo, lock["commit"]))
    if not expected or not (CLAUDE / "agents/muse.md").is_file():
        parser.error("missing committed Mars plugin output")
    existing = {p.relative_to(REFERENCE) for p in REFERENCE.rglob("*") if p.is_file()}
    stale = []
    for rel, data in expected.items():
        target = REFERENCE / rel
        if not target.is_file() or target.read_bytes() != data:
            stale.append(rel)
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    for rel in sorted(existing - expected.keys()):
        stale.append(rel)
        if not args.check:
            (REFERENCE / rel).unlink()
    if args.check and stale:
        parser.exit(1, "Stale Codex references:\n" + "\n".join(map(str, stale)) + "\n")
    print(f"Codex references: {len(expected)} source files verified" if args.check else
          f"Codex references: {len(stale)} files synchronized")


if __name__ == "__main__":
    main()
