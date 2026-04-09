# Claude Research Runner Implementation Plan

Date: 2026-04-09
Status: Pending approval

## 1. Delivery Goal

Implement the runner described in `docs/plans/claude-research-runner-spec.md` as a small packaged Python app, without starting the build until this plan is approved.

## 2. Implementation Sequence

### Phase 1: Scaffold package and runner directories

Deliverables:

- `pyproject.toml`
- `src/claude_research_runner/`
- `.gitignore` updates for runner state/log files
- basic CLI entrypoint

Tasks:

1. Create packaging metadata and console script.
2. Create module skeletons.
3. Create app directories for state and logs.
4. Add test package skeleton.

Exit criteria:

- `python -m claude_research_runner --help` works.

### Phase 2: Preflight and environment enforcement

Deliverables:

- Git root validation
- Claude binary detection
- subscription-auth validation
- dirty-worktree checks

Tasks:

1. Implement root detection and branch/upstream inspection.
2. Implement `claude auth status --text` parsing.
3. Reject startup if `README.md` is dirty.
4. Sanitize child environment to remove API-key auth variables.

Exit criteria:

- Runner fails early with actionable error messages for invalid environments.

### Phase 3: Claude execution engine

Deliverables:

- subprocess runner for `claude -p`
- streamed stdout/stderr handling
- per-phase NDJSON logs

Tasks:

1. Build command constructor for `research-new` and `research-complete`.
2. Stream stdout live to console while also logging raw lines.
3. Track child exit code and wall-clock runtime.
4. Support resume using stable session name.

Exit criteria:

- Fake Claude process can be executed and logged end-to-end.

### Phase 4: Limit detection and wait/resume

Deliverables:

- limit matcher
- reset parser
- waiting state persistence
- replay behavior

Tasks:

1. Implement regex-based limit detection.
2. Parse pipe-delimited epoch resets where available.
3. Persist waiting state and retry timestamp.
4. Replay the last unfinished phase after wake or process restart.

Exit criteria:

- Fake 5-hour and weekly limit outputs produce correct state transitions.

### Phase 5: Topic ID inference and phase verification

Deliverables:

- streamed topic extraction
- repo-diff validation
- phase completion checks

Tasks:

1. Implement `UC-\d{3}` extraction from Claude output.
2. Validate inferred topic ID against repo changes.
3. Implement research-new completion verification.
4. Implement research-complete completion verification.

Exit criteria:

- Runner can infer the topic ID safely from simulated output plus repo state.

### Phase 6: Git commit and push integration

Deliverables:

- scoped staging
- commit creation
- push with retry

Tasks:

1. Implement selective staging for the phase paths only.
2. Implement commit message generation.
3. Implement push to configured upstream.
4. Add transient retry logic for push failures.

Exit criteria:

- Temporary repo integration test proves commit and push behavior.

### Phase 7: Orchestrator wiring

Deliverables:

- end-to-end workflow controller
- state transitions
- clean terminal UX

Tasks:

1. Wire all modules into a single run loop.
2. Ensure every phase persists state before and after external operations.
3. Add clear console banners and summaries.
4. Ensure replay logic does not duplicate completed work.

Exit criteria:

- Fake end-to-end run completes both phases and Git steps.

### Phase 8: Tests and manual validation

Deliverables:

- unit tests
- fake Claude integration tests
- temp Git repo tests
- README snippet for usage

Tasks:

1. Add parser and verifier unit tests.
2. Add fake Claude integration scenarios.
3. Add Git preflight and push tests.
4. Run one manual smoke test with the real local Claude binary after implementation.

Exit criteria:

- Test suite passes locally.
- Manual smoke test passes or produces a concrete bug list.

## 3. Fake Claude Test Harness

The implementation should include a fake Claude executable for deterministic tests.

Planned scenarios:

1. `research-new` success with one `UC-###`
2. `research-new` output contains multiple IDs and must fail
3. `research-complete` success
4. 5-hour limit reached and delayed retry
5. weekly limit reached and repeated retry cycles
6. Claude exits non-zero without limit message
7. Claude partially writes files before interruption

## 4. Design Rules During Implementation

1. Use the spec’s headless-mode design unless you explicitly approve a different execution model.
2. Keep runtime dependencies at zero unless a non-stdlib dependency becomes clearly necessary.
3. Do not loosen the dirty-`README.md` preflight without explicit approval.
4. Do not add API-key-based fallback behavior.
5. Do not auto-stage unrelated changes.

## 5. Repo-Specific Warning for the Upcoming Build

Current repo state blocks the eventual automated run under the proposed safety rules because `README.md` is already modified.

That does not block implementation of the runner itself, but it will block a real end-to-end automated execution unless one of these happens later:

1. `README.md` is cleaned up before running the tool.
2. You explicitly approve a riskier patch-level staging strategy.

## 6. Validation Checklist Before Marking Implementation Done

1. The app launches `claude` with `--dangerously-skip-permissions`.
2. The app strips API-key auth from the child process.
3. The app uses `--effort max`.
4. The app runs `/research-new`.
5. The app infers a single valid `UC-###`.
6. The app runs `/research-complete UC-###`.
7. The app commits after each successful phase.
8. The app pushes after each successful phase.
9. The app pauses for 4 hours on limit detection and resumes the unfinished phase.
10. The app can recover from process restart using the state file.

## 7. Recommended Build Order for the Next Turn

When you ask to continue building, the next turn should do this:

1. Scaffold the package and CLI.
2. Implement preflight plus state persistence.
3. Implement Claude subprocess execution and stream logging.
4. Implement topic inference and verification.
5. Implement Git staging, commit, and push.
6. Add fake-Claude tests.
7. Run local tests.

## 8. Definition of Done

The task is complete when:

- the package is installable and runnable,
- tests cover the critical parser and resume paths,
- one end-to-end dry run with a fake Claude binary passes,
- one manual smoke test with the real local Claude binary is attempted,
- and the final behavior matches the approved spec.
