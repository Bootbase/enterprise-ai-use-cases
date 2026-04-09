# Claude Research Runner Spec

Date: 2026-04-09
Status: Draft for approval before implementation

## 1. Objective

Build a small packaged Python application that automates this Claude Code workflow from the repository root:

1. Start Claude Code using the locally installed `claude` binary.
2. Run the equivalent of `/effort max`.
3. Run `/research-new`.
4. Infer the generated topic ID from Claude output.
5. Run `/research-complete <topicId>`.
6. After each completed phase, commit and push the generated repo changes.
7. If Claude hits a subscription usage limit, stop, persist state, wait 4 hours, then retry the last unfinished command.

The application must use the local subscription-backed Claude Code installation, not the Anthropic API.

## 2. Key Constraints

### Functional constraints

- Must execute in the root of the current repository.
- Must use the local `claude` executable with `--dangerously-skip-permissions`.
- Must use Claude subscription auth, not API-key auth.
- Must support macOS and Windows.
- Must persist structured state to disk so a long-running one-shot process can survive pauses and restarts.
- Must show live console output while running.
- Must integrate with Git after each successful phase.

### Engineering constraints

- The runner must not depend on the Anthropic API directly.
- The runner must not require a PTY-driven full-screen TUI to work on Windows.
- The runner must not commit unrelated dirty worktree changes.

## 3. Chosen Execution Model

### Decision

The runner will use Claude Code headless print mode, not the full-screen interactive TUI.

### Why

- Official CLI docs support automation through `-p/--print`, `--output-format stream-json`, `--include-partial-messages`, `--continue`, `--resume`, and `--name`.
- This is materially more reliable on macOS and Windows than automating the Ink/TUI interface through a pseudo-terminal.
- It still uses the local `claude` binary and the user’s local subscription session.
- We can render the streamed output live to the console, which satisfies the practical "interactive" requirement without depending on TTY control hacks.

### Important equivalence note

- `/effort max` will be implemented as the documented CLI flag `--effort max`.
- `/research-new` and `/research-complete <topicId>` will be sent as Claude prompt text in headless mode.
- This is functionally equivalent to typing those commands inside Claude Code, while remaining scriptable and cross-platform.

## 4. Source-Backed Assumptions

These assumptions were verified on 2026-04-09.

### Local environment

- Installed binary: `/Users/sanderdecoster/.local/bin/claude`
- Installed version: `2.1.97 (Claude Code)`
- Current auth status: `Login method: Claude Max Account`

### Relevant official CLI behavior

- `claude -p "query"` is the supported non-interactive automation mode.
- `claude --continue` loads the most recent conversation in the current directory.
- `claude --resume <name-or-id>` resumes a specific named or identified session.
- `--name` sets a session name that can later be resumed.
- `--dangerously-skip-permissions` is documented and equivalent to `--permission-mode bypassPermissions`.
- `--output-format stream-json` and `--include-partial-messages` are documented for scripted real-time output.

### Relevant official usage-limit behavior

- Claude paid plans expose both a five-hour session limit and weekly limits.
- Claude Code and Claude web/app usage count against the same shared subscription limits.
- Official guidance says users can monitor remaining allocation with `/status`.
- Official guidance also says `ANTHROPIC_API_KEY` causes Claude Code to use API billing instead of subscription usage.

### Observed Claude Code limit strings from public issue reports

These are not official contracts, but they are useful observed patterns:

- `5-hour limit reached ∙ resets 12pm`
- `Opus weekly limit reached ∙ resets Oct 31, 9am`
- `Claude AI usage limit reached|1760004000`

The runner will treat these as heuristics, not a formal API.

## 5. Repo-Specific Observations

At spec time, this repository is not clean:

- `README.md` is already modified.
- Multiple untracked use-case folders already exist.

That matters because both `/research-new` and `/research-complete` will change `README.md`, and Git automation must avoid committing unrelated changes.

## 6. Preflight Rules

The runner will perform these checks before starting:

1. Current working directory must be a Git repository root.
2. `claude` must be present on `PATH` or be explicitly provided.
3. `claude auth status --text` must report a Claude subscription-backed login.
4. `ANTHROPIC_API_KEY` must not be present in the child process environment.
5. The current branch must exist and have a push remote configured.
6. `README.md` must be clean before the run starts.
7. If a target use-case folder already exists before a `research-complete` phase begins, it must be clean.

### Hard stop behavior

The runner will refuse to start if `README.md` is already dirty.

Reason: staging `README.md` safely after automation is otherwise ambiguous and risks committing unrelated user changes.

## 7. Runner UX

### Command shape

The package will expose a CLI entrypoint:

```bash
python -m claude_research_runner run
```

Equivalent installed command:

```bash
claude-research-runner run
```

### Initial CLI options

- `run`
- `--root <path>`: defaults to current working directory
- `--claude-bin <path>`: defaults to `claude`
- `--sleep-hours <int>`: defaults to `4`
- `--session-name <name>`: optional; default auto-generated per run
- `--git-remote <name>`: defaults to tracked upstream remote
- `--no-push`: optional safety switch for local-only dry runs
- `--resume-state <path>`: optional explicit state resume

### Console behavior

- Print a concise phase banner when each step starts.
- Stream Claude output live to stdout.
- Print limit-detection messages clearly.
- Print commit SHA and push target after each successful Git phase.
- Print state-file path whenever the runner pauses or exits.

## 8. Claude Invocation Strategy

### Session naming

The runner will create a stable Claude session name per run, for example:

```text
claude-research-runner-20260409T153012Z
```

This avoids relying on undocumented stream event fields for session identity.

### Command 1: research-new

```bash
claude \
  --dangerously-skip-permissions \
  --effort max \
  --name "<run-session-name>" \
  --print \
  --output-format stream-json \
  --include-partial-messages \
  "/research-new"
```

### Command 2: research-complete

```bash
claude \
  --dangerously-skip-permissions \
  --effort max \
  --resume "<run-session-name>" \
  --print \
  --output-format stream-json \
  --include-partial-messages \
  "/research-complete UC-XXX"
```

### Retry after limit or crash

The runner will resume the named Claude session and replay the last unfinished phase command.

## 9. Workflow State Machine

The runner will implement this state machine:

1. `preflight`
2. `research_new_running`
3. `research_new_verifying`
4. `research_new_git`
5. `research_complete_running`
6. `research_complete_verifying`
7. `research_complete_git`
8. `waiting_for_limit_reset`
9. `completed`
10. `failed`

### Replay rule

On restart, the runner will:

1. Load persisted state.
2. Verify whether the last phase already completed on disk.
3. If complete, advance to the Git step or next phase.
4. If incomplete, replay the last unfinished Claude command.

This avoids duplicate progression if Claude already wrote the needed files before the process stopped.

## 10. Topic ID Inference

The topic ID will be inferred from `/research-new` output, then validated against repository changes.

### Primary extraction

Regex search over streamed Claude output:

```text
\bUC-\d{3}\b
```

### Secondary validation

After `/research-new` exits, validate by inspecting repo changes:

- New folder matching `use-cases/**/UC-###-*/use-case.md`
- Updated `README.md` row containing the same `UC-###`
- `use-case.md` present and status remains `research`

### Ambiguity rule

If zero or multiple distinct topic IDs are found and validation cannot disambiguate them, the runner will fail fast instead of guessing.

## 11. Phase Completion Rules

### research-new is complete when all are true

- A single `UC-###` topic ID is known.
- A matching use-case folder exists.
- `use-case.md` exists in that folder.
- `README.md` contains a new row for that topic ID.

### research-complete is complete when all are true

- `solution-design.md` exists.
- `implementation-guide.md` exists.
- `evaluation.md` exists.
- `references.md` exists.
- `use-case.md` status is updated to `detailed`.
- `README.md` row status is updated to `detailed`.

## 12. Limit Detection and Pause Logic

### Detection inputs

The runner will scan:

- Claude stdout event payloads
- Claude stderr
- Process exit text

### Limit patterns

The initial matcher set will include:

- `5-hour limit reached`
- `weekly limit reached`
- `usage limit reached`
- `resets`
- `Claude AI usage limit reached|`

Matching will be case-insensitive.

### Reset parsing

The runner will support three cases:

1. Human-readable reset text like `resets 12pm`
2. Human-readable reset text like `resets Oct 31, 9am`
3. Pipe-delimited epoch form like `Claude AI usage limit reached|1760004000`

### Wait policy

- The default retry delay is 4 hours, per user requirement.
- If a parsed reset time is later than 4 hours from now, the runner will still wake every 4 hours and retry.
- If a parsed reset time is sooner than 4 hours, the runner will still honor the user requirement and wait 4 hours.

### Practical consequence

- Five-hour limits will usually clear by the next retry.
- Weekly limits may require repeated 4-hour wake/retry cycles until the reset window actually passes.

## 13. Git Integration

### High-level behavior

After each successful phase, the runner will:

1. Verify the files attributable to that phase.
2. Stage only those files.
3. Create a commit.
4. Push to the current tracked branch.

### Staging policy

#### After research-new

Stage only:

- `README.md`
- The newly created `use-cases/**/UC-###-*/` folder

#### After research-complete

Stage only:

- `README.md`
- The target `use-cases/**/UC-###-*/` folder

### Commit message policy

#### research-new

```text
chore(research): add UC-### via claude runner
```

#### research-complete

```text
chore(research): complete UC-### via claude runner
```

### Push policy

- Push to the branch’s configured upstream.
- If no upstream exists, fail preflight.
- If push fails due to transient error, retry up to 3 times with backoff.
- If push still fails, persist state and exit `failed`.

### What will not be committed

- Runner logs
- Runner state files
- Unrelated user changes
- Pre-existing dirty files outside the phase scope

## 14. State File

The runner will persist a structured JSON state file in:

```text
.claude-research-runner/state.json
```

### Example shape

```json
{
  "version": 1,
  "run_id": "20260409T153012Z",
  "root": "/abs/path/to/repo",
  "session_name": "claude-research-runner-20260409T153012Z",
  "current_phase": "research_complete_running",
  "topic_id": "UC-059",
  "last_command": "/research-complete UC-059",
  "sleep_hours": 4,
  "limit_retries": 1,
  "waiting_until": "2026-04-09T19:30:00Z",
  "git": {
    "branch": "main",
    "upstream": "origin/main",
    "last_commit": "abc1234"
  },
  "artifacts": {
    "research_new_folder": "use-cases/.../UC-059-.../",
    "logs_dir": ".claude-research-runner/logs"
  },
  "timestamps": {
    "started_at": "2026-04-09T15:30:12Z",
    "updated_at": "2026-04-09T16:47:03Z"
  }
}
```

## 15. Logging

The runner will write:

- `.claude-research-runner/state.json`
- `.claude-research-runner/logs/research-new.ndjson`
- `.claude-research-runner/logs/research-complete.ndjson`
- `.claude-research-runner/logs/git.log`
- `.claude-research-runner/logs/runner.log`

These files must be `.gitignore`d during implementation.

## 16. Package Layout

Planned structure:

```text
pyproject.toml
src/
  claude_research_runner/
    __init__.py
    cli.py
    app.py
    config.py
    state.py
    models.py
    claude_exec.py
    event_stream.py
    limit_detection.py
    topic_inference.py
    verification.py
    git_ops.py
    console.py
tests/
  test_limit_detection.py
  test_topic_inference.py
  test_verification.py
  test_git_ops.py
  test_workflow_resume.py
```

### Dependency policy

V1 should be stdlib-only if possible:

- `argparse`
- `subprocess`
- `threading`
- `queue`
- `json`
- `pathlib`
- `datetime`
- `re`
- `time`

No runtime dependency is required if we stay in headless mode.

## 17. Failure Handling

### Fail fast cases

- `claude` missing
- Claude auth is API/Console-based instead of subscription-based
- `README.md` dirty at startup
- Topic ID cannot be inferred safely
- Phase verification fails after Claude exits
- Git commit or push fails permanently

### Recoverable cases

- Claude usage limit reached
- Network failure during push, within retry budget
- Process interruption, if state file exists

## 18. Testing Strategy

### Unit tests

- Limit string parsing
- Reset-time extraction
- Topic ID extraction from output
- Phase verification from filesystem state
- Git staging path selection

### Integration tests with fake Claude binary

Use a fake executable to simulate:

- Successful `/research-new`
- Successful `/research-complete`
- 5-hour limit reached
- Weekly limit reached
- Partial output then crash

### Git integration tests

Use temporary repositories with a bare remote to verify:

- Commit creation
- Push success
- Preflight rejection on dirty `README.md`

### Real-world manual smoke test

Run one manual end-to-end validation on macOS using the installed `claude` binary after implementation.

## 19. Acceptance Criteria

The implementation will be accepted when all are true:

1. Running `claude-research-runner run` from the repo root uses the local `claude` binary only.
2. The child Claude process is launched with `--dangerously-skip-permissions`.
3. The runner does not use API-key auth.
4. `/research-new` is executed and the resulting `UC-###` is inferred correctly.
5. `/research-complete <topicId>` is executed against the inferred topic.
6. After each phase, the correct files are committed and pushed.
7. If a limit is reached, the runner persists state, waits 4 hours, and retries the unfinished phase.
8. The workflow can be resumed after process restart from the saved state file.
9. The same implementation works on macOS and Windows.

## 20. Risks and Deliberate Tradeoffs

### Tradeoff 1: no full-screen TUI automation

This is intentional. Headless Claude CLI is the reliable path for Mac+Windows support.

### Tradeoff 2: strict dirty-worktree preflight

This is also intentional. Safe Git automation is more important than permissive startup in a dirty repo.

### Tradeoff 3: 4-hour retry cadence

This exactly follows the user requirement, but weekly limits may still require multiple retry cycles.

## 21. References

Official sources used for this spec:

- Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference
- Using Claude Code with your Pro or Max plan: https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan
- How do usage and length limits work?: https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work
- Usage limit best practices: https://support.claude.com/en/articles/9797557-usage-limit-best-practices

Observed public issue examples used only as heuristics:

- https://github.com/anthropics/claude-code/issues/6457
- https://github.com/anthropics/claude-code/issues/10333
- https://github.com/anthropics/claude-code/issues/8835
