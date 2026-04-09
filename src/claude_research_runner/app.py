from __future__ import annotations

import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

from .claude_exec import run_claude
from .config import AppConfig
from .console import banner, error, info, warn
from .git_ops import (
    GitError,
    commit,
    current_branch,
    dirty_paths,
    ensure_repo_root,
    has_path_changes,
    push,
    stage_paths,
    upstream_ref,
)
from .models import Phase, RunState
from .state import default_state, load_state, save_state
from .topic_inference import extract_topic_ids
from .verification import find_use_case_dirs, verify_research_complete, verify_research_new


class RunnerError(RuntimeError):
    pass


def _read_claude_auth_status(root: Path, claude_bin: str) -> str:
    from subprocess import run

    completed = run(
        [claude_bin, "auth", "status", "--text"],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RunnerError(completed.stderr.strip() or completed.stdout.strip() or "Failed to read Claude auth status")
    return completed.stdout


def _ensure_claude_available(claude_bin: str) -> None:
    if shutil.which(claude_bin) is None and not Path(claude_bin).exists():
        raise RunnerError(f"Claude binary not found: {claude_bin}")


def _parse_login_method(status_text: str) -> str | None:
    for line in status_text.splitlines():
        if line.lower().startswith("login method:"):
            return line.split(":", 1)[1].strip()
    return None


def _load_or_create_state(config: AppConfig) -> tuple[RunState, bool]:
    state = load_state(config.state_path)
    if state and state.current_phase not in {Phase.COMPLETED, Phase.FAILED}:
        if Path(state.root).resolve() != config.root.resolve():
            raise RunnerError(f"State file root {state.root} does not match requested root {config.root}")
        info(f"Resuming workflow from {config.state_path}")
        state.sleep_hours = config.sleep_hours
        return state, True

    shutil.rmtree(config.state_path.parent, ignore_errors=True)
    return default_state(config.root, config.session_name, config.sleep_hours), False


def _phase_log_path(config: AppConfig, state: RunState, phase_name: str) -> Path:
    return config.logs_dir / f"{phase_name}.ndjson"


def _infer_topic_id_from_log(log_path: Path, root: Path) -> str:
    if not log_path.exists():
        raise RunnerError(f"Log file does not exist: {log_path}")
    texts: list[str] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            import json

            payload = json.loads(line)
        except Exception:
            continue
        for key in ("rendered", "raw"):
            value = payload.get(key)
            if isinstance(value, str):
                texts.append(value)

    candidates = extract_topic_ids("\n".join(texts))
    if not candidates:
        raise RunnerError("Could not infer a topic ID from Claude output")

    valid = [candidate for candidate in candidates if find_use_case_dirs(root, candidate)]
    if len(valid) == 1:
        return valid[0]
    if len(candidates) == 1:
        return candidates[0]
    raise RunnerError(f"Could not disambiguate inferred topic IDs: {', '.join(candidates)}")


def _mark_failed(config: AppConfig, state: RunState, message: str) -> int:
    error(message)
    state.current_phase = Phase.FAILED
    state.failure_message = message
    save_state(config.state_path, state)
    return 1


def _fresh_preflight(config: AppConfig, state: RunState) -> None:
    _ensure_claude_available(config.claude_bin)
    ensure_repo_root(config.root)

    auth_text = _read_claude_auth_status(config.root, config.claude_bin)
    login_method = _parse_login_method(auth_text)
    if not login_method or not login_method.startswith("Claude "):
        raise RunnerError(f"Unsupported Claude auth mode: {login_method or 'unknown'}")

    readme_dirty = dirty_paths(config.root, "README.md")
    if readme_dirty:
        raise RunnerError("README.md is already dirty; refusing to start unsafe automated staging")

    branch = current_branch(config.root)
    upstream = upstream_ref(config.root)
    if not config.no_push and not (config.git_remote or upstream):
        raise RunnerError("Current branch has no upstream and no --git-remote was provided")

    state.git.branch = branch
    state.git.upstream = upstream
    state.git.push_remote = config.git_remote or (upstream.split("/", 1)[0] if upstream else None)
    state.artifacts.logs_dir = str(config.logs_dir)
    state.current_phase = Phase.RESEARCH_NEW_RUNNING
    save_state(config.state_path, state)


def _resume_wait(config: AppConfig, state: RunState) -> None:
    target = None
    if state.waiting_until:
        target = datetime.fromisoformat(state.waiting_until)
    if target is None:
        target = datetime.now().astimezone() + timedelta(hours=state.sleep_hours)
    remaining = (target - datetime.now().astimezone()).total_seconds()
    if remaining > 0:
        info(f"Sleeping for {remaining:.0f}s before retrying {state.resume_phase.value if state.resume_phase else 'workflow'}")
        time.sleep(remaining)
    state.waiting_until = None
    if state.resume_phase is None:
        raise RunnerError("State is waiting for a retry but no resume_phase is recorded")
    state.current_phase = state.resume_phase
    state.resume_phase = None
    save_state(config.state_path, state)


def _schedule_retry(config: AppConfig, state: RunState, phase: Phase, message: str) -> None:
    warn(message)
    state.current_phase = Phase.WAITING_FOR_LIMIT_RESET
    state.resume_phase = phase
    state.limit_retries += 1
    state.waiting_until = (datetime.now().astimezone() + timedelta(hours=state.sleep_hours)).isoformat()
    save_state(config.state_path, state)


def _run_phase(config: AppConfig, state: RunState, phase: Phase, command_text: str) -> bool:
    resume_session = state.session_started
    if phase == Phase.RESEARCH_NEW_RUNNING and not state.session_started:
        state.session_started = True

    state.current_phase = phase
    state.last_command = command_text
    save_state(config.state_path, state)

    phase_name = "research-new" if phase == Phase.RESEARCH_NEW_RUNNING else "research-complete"
    log_path = _phase_log_path(config, state, phase_name)
    result = run_claude(
        claude_bin=config.claude_bin,
        root=config.root,
        session_name=state.session_name,
        command_text=command_text,
        log_path=log_path,
        resume_session=resume_session,
    )

    if result.limit_hit is not None:
        _schedule_retry(config, state, phase, f"Claude usage limit hit: {result.limit_hit.matched_text}")
        return False
    if result.exit_code != 0:
        raise RunnerError(f"Claude exited with code {result.exit_code}: {result.stderr_text or result.raw_output}")

    state.current_phase = (
        Phase.RESEARCH_NEW_VERIFYING if phase == Phase.RESEARCH_NEW_RUNNING else Phase.RESEARCH_COMPLETE_VERIFYING
    )
    save_state(config.state_path, state)
    return True


def _commit_phase(config: AppConfig, state: RunState, *, message: str, paths: list[str]) -> None:
    stage_paths(config.root, paths)
    commit_sha = commit(config.root, message)
    if commit_sha:
        info(f"Created commit {commit_sha}")
        state.git.last_commit = commit_sha
    elif has_path_changes(config.root, paths):
        info("Relevant paths remain dirty but no new commit was created; assuming commit step is already satisfied")
    else:
        info("No changes to commit for this phase")

    if not config.no_push and state.git.push_remote and state.git.branch and commit_sha:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                push(config.root, state.git.push_remote, state.git.branch)
                info(f"Pushed {state.git.branch} to {state.git.push_remote}")
                last_error = None
                break
            except GitError as exc:
                last_error = exc
                warn(f"Push attempt {attempt}/3 failed: {exc}")
                if attempt < 3:
                    time.sleep(attempt)
        if last_error is not None:
            raise last_error
    save_state(config.state_path, state)


def run_workflow(config: AppConfig) -> int:
    state, _ = _load_or_create_state(config)
    save_state(config.state_path, state)

    try:
        while True:
            if state.current_phase == Phase.PREFLIGHT:
                banner("Preflight")
                _fresh_preflight(config, state)
                continue

            if state.current_phase == Phase.WAITING_FOR_LIMIT_RESET:
                banner("Waiting For Limit Reset")
                _resume_wait(config, state)
                continue

            if state.current_phase == Phase.RESEARCH_NEW_RUNNING:
                banner("Research New")
                if not _run_phase(config, state, Phase.RESEARCH_NEW_RUNNING, "/research-new"):
                    continue
                continue

            if state.current_phase == Phase.RESEARCH_NEW_VERIFYING:
                banner("Verify Research New")
                if state.topic_id is None:
                    state.topic_id = _infer_topic_id_from_log(_phase_log_path(config, state, "research-new"), config.root)
                verification = verify_research_new(config.root, state.topic_id)
                state.artifacts.research_new_folder = verification.use_case_dir
                state.current_phase = Phase.RESEARCH_NEW_GIT
                save_state(config.state_path, state)
                continue

            if state.current_phase == Phase.RESEARCH_NEW_GIT:
                banner("Git Commit Research New")
                if not state.topic_id or not state.artifacts.research_new_folder:
                    raise RunnerError("Missing topic_id or use case folder before research-new Git step")
                _commit_phase(
                    config,
                    state,
                    message=f"chore(research): add {state.topic_id} via claude runner",
                    paths=["README.md", state.artifacts.research_new_folder],
                )
                state.current_phase = Phase.RESEARCH_COMPLETE_RUNNING
                save_state(config.state_path, state)
                continue

            if state.current_phase == Phase.RESEARCH_COMPLETE_RUNNING:
                banner("Research Complete")
                if not state.topic_id:
                    raise RunnerError("Cannot run research-complete without a topic_id")
                if not _run_phase(
                    config,
                    state,
                    Phase.RESEARCH_COMPLETE_RUNNING,
                    f"/research-complete {state.topic_id}",
                ):
                    continue
                continue

            if state.current_phase == Phase.RESEARCH_COMPLETE_VERIFYING:
                banner("Verify Research Complete")
                if not state.topic_id:
                    raise RunnerError("Cannot verify research-complete without a topic_id")
                verification = verify_research_complete(config.root, state.topic_id)
                state.artifacts.research_new_folder = verification.use_case_dir
                state.current_phase = Phase.RESEARCH_COMPLETE_GIT
                save_state(config.state_path, state)
                continue

            if state.current_phase == Phase.RESEARCH_COMPLETE_GIT:
                banner("Git Commit Research Complete")
                if not state.topic_id or not state.artifacts.research_new_folder:
                    raise RunnerError("Missing topic_id or use case folder before research-complete Git step")
                _commit_phase(
                    config,
                    state,
                    message=f"chore(research): complete {state.topic_id} via claude runner",
                    paths=["README.md", state.artifacts.research_new_folder],
                )
                state.current_phase = Phase.COMPLETED
                save_state(config.state_path, state)
                info(f"Workflow completed successfully. State saved to {config.state_path}")
                return 0

            if state.current_phase == Phase.COMPLETED:
                info(f"Workflow already completed. State saved to {config.state_path}")
                return 0

            if state.current_phase == Phase.FAILED:
                return _mark_failed(config, state, state.failure_message or "Workflow is already marked failed")

            raise RunnerError(f"Unhandled phase: {state.current_phase}")

    except (RunnerError, GitError) as exc:
        return _mark_failed(config, state, str(exc))
