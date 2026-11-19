# Installation

Python 3.11+ on POSIX. Locked CLI into its own environment:

```sh
UV_PROJECT_ENVIRONMENT=~/.local/share/drive-sync-venv uv sync --locked --no-editable --project ~/.gemini/config/plugins/creative-writing-skills/skills/writing-sync
~/.local/share/drive-sync-venv/bin/drive-sync --help
```

Use that binary. Do not import from the skill source. Indexes, sources, state,
and OAuth profiles stay outside the skill. Install does not authorize Google
writes.
