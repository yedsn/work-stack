# Project Context

## Purpose
Work Stack is a cross-platform desktop launcher that lets power users group applications, scripts, and web resources into curated tabs with tagging, filtering, and remote sync. The goal is a low-latency, keyboard-friendly UI that resumes instantly even with hundreds of launch targets.

## Tech Stack
- Python 3.10+
- PyQt5 for GUI
- `keyboard`/platform-specific hotkey managers
- JSON-based configuration persisted via `utils.config_manager`
- OpenSpec for requirements and change management

## Project Conventions

### Code Style
- Python: 4-space indentation, UTF-8 encoding, `snake_case` functions/vars, `PascalCase` classes.
- UI objects named descriptively (`self.loading_overlay`, `self.stats_label`).
- Keep modules under ~500 lines when practical; split reusable logic into `utils/`.

### Architecture Patterns
- `gui/` owns presentation (widgets, dialogs, hotkey wiring). Avoid business logic here beyond orchestration.
- `utils/` provides single-source-of-truth services (config, logging, sync, history). GUI talks to these via helper APIs to keep state consistent.
- Configuration updates flow through debounced helpers and background threads; visible refreshes go through `update_ui_with_config`.
- Specs drive changes: every behavioral shift should add/modify an OpenSpec capability before coding.

### Testing Strategy
- Use Python `unittest` for integration-style checks (e.g., `tests/test_deferred_refresh.py`).
- Prefer real LaunchGUI instances when feasible; stub long-running sync operations rather than mocking PyQt internals.
- Manual smoke: launch via `python main.py`, exercise hotkeys, sync, and tag filters before release.

### Git Workflow
- Feature/change IDs follow verb-led kebab case (`update-background-refresh-flow`).
- Keep commits small, imperative, and reference change IDs when touching specs.
- PRs must list user-visible impact plus manual/automated tests; block merges until `openspec validate <id> --strict` passes.

## Domain Context
- Users rely on instant resume: avoid blocking UI when hidden; background sync should only mark pending state.
- Config has local-only keys (window sizes, tag filters) that should not leak to sync services; always use `prepare_config_for_sync`.

## Important Constraints
- No secrets or credentials in Git; `credentials.enc` stays encrypted.
- Global hotkeys differ per platform; modify Windows/macOS/Linux hotkey managers cautiously and guard platform-specific imports.
- Launcher must stay responsive with >100 launch items, so batch UI updates (`begin_batch_update`/`end_batch_update`) when possible.

## External Dependencies
- GitHub Gist, Open Gist, and WebDAV are optional sync targets; always handle failures gracefully and respect `sync_settings`.
- System tray APIs differ across platforms; test show/hide flows on Windows primarily, keep macOS/Linux stubs aligned with existing patterns.
