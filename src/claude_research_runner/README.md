# Claude Research Runner

`claude_research_runner` is a small Python CLI for this repository that drives the local subscription-backed `claude` CLI through the `research-new` and `research-complete` workflow in a loop.

It does not use the Claude API. It shells out to your local `claude` binary with `--dangerously-skip-permissions`, runs in the repository root, persists workflow state, and commits/pushes the generated use-case files after each phase.

## What It Does

The tool will:

1. verify that `claude` is installed and authenticated with a Claude account
2. start or resume a Claude session in print/stream-json mode
3. run the equivalent of:
   - `/effort max`
   - `/research-new`
   - `/research-complete <topicId>`
4. infer the `topicId` from Claude output and the new use-case directory
5. verify the generated files
6. commit and optionally push:
   - the repo root `README.md`
   - the generated `use-cases/.../UC-...` directory
7. if Claude hits a resettable usage limit, wait and retry the unfinished phase
8. after a successful `research-complete`, start the full process again
9. stop only when:
   - you stop the process
   - Claude hits a weekly limit
   - the configured max runtime is reached

## Prerequisites

- Python 3.11+
- `claude` installed locally and available on `PATH`
- `claude auth status --text` must show a Claude account login method
- Git repository with a configured upstream branch, unless you pass `--git-remote` or `--no-push`
- Run from this repository root, not a subdirectory

## Install

From the repository root:

```bash
python -m pip install -e .
```

That installs the console script:

```bash
claude-research-runner
```

You can also run it without installing the script:

```bash
PYTHONPATH=src python -m claude_research_runner run
```

## Quick Start

From the repository root:

```bash
claude-research-runner run --root .
```

If you prefer module execution:

```bash
PYTHONPATH=src python -m claude_research_runner run --root .
```

This is the normal path for a real run:

```bash
claude-research-runner run --root . --sleep-hours 4 --max-runtime-hours 24
```

## Common Commands

Run with default settings:

```bash
claude-research-runner run --root .
```

Commit locally but do not push:

```bash
claude-research-runner run --root . --no-push
```

Use an explicit remote:

```bash
claude-research-runner run --root . --git-remote origin
```

Resume from an alternate state file:

```bash
claude-research-runner run --root . --resume-state /path/to/state.json
```

Use a non-default Claude binary:

```bash
claude-research-runner run --root . --claude-bin /path/to/claude
```

Run for 8 hours instead of the default 24:

```bash
claude-research-runner run --root . --max-runtime-hours 8
```

## CLI Arguments

`claude-research-runner run` supports:

- `--root`
  Repository root. Defaults to the current directory.
- `--claude-bin`
  Claude binary to execute. Defaults to `claude`.
- `--sleep-hours`
  Hours to wait before retrying after a Claude limit hit. Defaults to `4`.
- `--max-runtime-hours`
  Maximum total runtime for the looping app before it stops cleanly. Defaults to `24`.
- `--session-name`
  Optional explicit Claude session name.
- `--git-remote`
  Remote to push to. If omitted, the tracked upstream remote is used.
- `--no-push`
  Commit locally without pushing.
- `--resume-state`
  Alternate path for the persisted state file.

## How Resume Works

The runner persists state in:

```text
.claude-research-runner/state.json
```

If a run stops partway through because of an interruption or a resettable Claude limit, rerun the same command. The runner will load the saved phase and continue from there.

For Claude print-mode resume, the runner recovers the real Claude session UUID from the saved logs and uses that for `--resume`.

After a fully successful cycle, the runner resets its internal phase state and starts a brand-new cycle until one of the stop conditions is hit.

## Logs And Artifacts

The runner writes under:

```text
.claude-research-runner/
```

Important files:

- `.claude-research-runner/state.json`
  Current workflow state
- `.claude-research-runner/logs/research-new.ndjson`
  Streamed Claude output for `research-new`
- `.claude-research-runner/logs/research-complete.ndjson`
  Streamed Claude output for `research-complete`
- `.claude-research-runner/baselines/`
  Internal snapshots used to safely handle pre-existing `README.md` edits and detect pre-existing use-case directories

## Git Behavior

After a successful `research-new`, the runner commits and pushes:

- the generated `UC-...` directory
- the root `README.md` delta for that phase

After a successful `research-complete`, it does the same again.

Commit messages are:

- `chore(research): add UC-XXX via claude runner`
- `chore(research): complete UC-XXX via claude runner`

Then, unless stopped by a runtime ceiling or a weekly limit, it starts the next `research-new` cycle automatically.

## Dirty Root README

If the repository root `README.md` is already dirty before a fresh run:

- the runner snapshots your current `README.md`
- temporarily restores the worktree copy to `HEAD`
- runs Claude and stages only the generated `README.md` delta for the automated commit
- restores your original `README.md` edits afterward

If your local `README.md` changes overlap heavily with Claude's generated delta, restoration can still produce merge conflicts.

## Guardrails And Assumptions

- This tool is repo-specific. It expects this repository layout and the existing `research-new` / `research-complete` skills.
- It refuses to commit a use-case directory that already existed before the run started.
- It assumes the repository root is the working directory for Claude and Git operations.
- It is designed around the local Claude CLI, not API-based automation.
- Shorter Claude usage limits are treated as retryable; weekly limits stop the app.

## Troubleshooting

`Claude binary not found`

- Verify `claude` is installed and on `PATH`, or pass `--claude-bin`.

`Unsupported Claude auth mode`

- Run `claude auth status --text` and make sure you are logged in with a Claude account.

`Current branch has no upstream`

- Set an upstream branch or pass `--git-remote`.

`Claude session_id is required to resume in print mode`

- Ensure the previous phase wrote its `.ndjson` log under `.claude-research-runner/logs/`.

Run marked `waiting_for_limit_reset`

- Rerun the same command and let the runner sleep until the saved retry time, or adjust `--sleep-hours` for future runs.

Run stops after a successful cycle even though you expected it to continue

- Check `--max-runtime-hours`. The app now stops cleanly once that total runtime budget is exhausted.

Run stops on a weekly limit

- That is intentional. Weekly limits are terminal for the current app run.

## Typical Real Run

```bash
claude-research-runner run --root . --sleep-hours 4 --max-runtime-hours 24
```

Then monitor:

- console output for live Claude progress
- `.claude-research-runner/state.json` for phase/status
- `.claude-research-runner/logs/*.ndjson` for raw streamed output
