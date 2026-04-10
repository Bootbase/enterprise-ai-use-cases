# AI Agent Instructions

## Scope

This repo is a catalog of real-world Enterprise AI Case Studies — each researched, designed, and documented end-to-end. Each case study follows a lifecycle: `research` → `detailed`.

## Navigation

| I need to...                              | Action                                                                                         |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Add a new case study                      | Read [.agents/skills/research-new/SKILL.md](.agents/skills/research-new/SKILL.md)             |
| Detail an existing `research` case study  | Read [.agents/skills/research-complete/SKILL.md](.agents/skills/research-complete/SKILL.md)   |
| Browse the case study index               | Read [docs/use-cases/README.md](docs/use-cases/README.md)                                      |
| Understand the file structure             | Read [.agents/templates/](.agents/templates/)                                                 |
| See reusable prompts (copy-paste format)  | Read [docs/PROMPT.md](docs/PROMPT.md)                                                         |

## Case Study Lifecycle

```
research-new                     research-complete
      │                                │
      ▼                                ▼
┌──────────┐                   ┌──────────────┐
│ research │ ─────────────────▸│   detailed   │
│          │                   │              │
│ Files:   │                   │ Files:       │
│ • docs/use-cases/{category}/  │ • docs/use-cases/{category}/
│   UC-NNN-slug/index.md        │   UC-NNN-slug/index.md (status updated)
│          │                   │ • solution-design.md
│          │                   │ • implementation-guide.md
│          │                   │ • evaluation.md
│          │                   │ • references.md
└──────────┘                   └──────────────┘
```

## Automated Runner

The `research-runner` CLI can drive any supported agent backend through the case study workflow in a loop. See [src/research_runner/README.md](src/research_runner/README.md).

```bash
# Claude (default)
research-runner run --root . --sleep-hours 4 --max-runtime-hours 24

# Codex
research-runner run --root . --backend codex --max-runtime-hours 24
```

## Loading Priority

1. Load this file at session start.
2. Check the navigation table before starting work — load the matching skill from `.agents/skills/`.
3. `.claude/skills/` mirrors `.agents/skills/` via symlink (for Claude Code).
4. Load templates and PROMPT.md on demand.
