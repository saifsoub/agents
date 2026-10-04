# agents (Seif's fork) — plain-language README

## What this is
This is Seif's copy (a "fork") of **livekit/agents**, a Python framework for building AI agents you can talk to live by voice (and video). LiveKit is the real-time audio and video service underneath it.

## Who it's for
Developers who want to build voice assistants, phone agents, or other live AI conversations.

## What it does today
Upstream: the main framework, plus plug-ins for speech, AI model and voice providers, plus examples.

**Seif's changes vs upstream** (late July to end of August 2026). Seif added his own team-and-process layer on top:
- **`documentation/`**: a documentation "team" with a style standard and named worker roles (Documentation Architect, Knowledge Curator, Documentation Editor, Style Guardian, Notion Systems Specialist, Documentation Publisher, Documentation QA), each described in `documentation/workers/`.
- **`aria/`**: an "Aria" system file and `aria/ROUTING.md`, which says which team handles which kind of request.
- **PR #2, "Add governed cross-functional S/Squad team"**: added `teams/squad/` (`TEAM.md`, `team.json`, `runtime.py`), a test `tests/test_squad_team.py`, and an issue form `.github/ISSUE_TEMPLATE/squad_work.yaml`, and updated `aria/ROUTING.md`.
- How these files connect to the LiveKit voice code, if at all: not yet confirmed.

## How to run it
Install the framework with `pip install livekit-agents` (the extras each plug-in needs: not yet confirmed here). For a voice agent you need a LiveKit server or account plus keys for your AI providers. Keep keys out of the repo. To try Seif's squad test: `pytest tests/test_squad_team.py` (whether it passes: not yet confirmed).

## Current status and known gaps
- There are 2 open issues on this fork.
- Whether Seif's team files are used by anything running: not yet confirmed.

## Where things live
| Folder / file | What's in it |
|---|---|
| `livekit-agents/` | The main framework |
| `livekit-plugins/` | Add-ons for speech and AI providers |
| `examples/` | Example agents |
| `tests/` | Tests, including Seif's squad test |
| `documentation/` | Seif's documentation team |
| `aria/` | Seif's Aria routing |
| `teams/squad/` | Seif's S/Squad team |
| `LICENSE`, `NOTICE` | Apache-2.0 |
