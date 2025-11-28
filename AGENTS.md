<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Repository Guidelines

## Project Structure & Module Organization
- `gui/` contains the PyQt5 interface (main window, widgets, dialogs). Keep UI-specific assets such as images under `resources/`.
- `utils/` holds shared services: configuration, logging, sync helpers, and platform settings. Treat these modules as the single source of truth for cross-GUI logic.
- `openspec/` tracks specs, proposals, and tasks. Use `openspec/changes/<id>/` while iterating and move deltas to `openspec/specs/` only after deployment.
- `tests/` houses Python-based regression and performance checks. Add any new automation here using the existing naming style.

## Build, Test, and Development Commands
- `python main.py` �� launches the desktop app locally using the default config.
- `python -m unittest` or `python -m unittest tests.test_deferred_refresh` �� runs the complete or targeted test suite.
- `openspec validate <change-id> --strict` �� verifies proposal/spec deltas before requesting review.
- `rg <pattern> -n <path>` �� preferred search utility for locating symbols or requirements quickly.

## Coding Style & Naming Conventions
- Python code follows 4-space indentation, UTF-8 encoding, and standard PEP8 readability (even if tooling is manual).
- Use `snake_case` for functions, methods, and local variables; `PascalCase` for classes (e.g., `LaunchGUI`).
- Qt object properties should be descriptive (`self.loading_overlay`, `self.stats_label`). File names stay lowercase with underscores (`config_manager.py`).

## Testing Guidelines
- Prefer Python's built-in `unittest` framework for GUI-adjacent logic. Mirror the pattern in `tests/test_deferred_refresh.py` when adding new cases.
- Name tests after the capability or feature under validation (`test_background_refresh_is_applied_on_demand`).
- Verify both visible and background flows; when feasible, stub long-running operations rather than mocking PyQt internals.

## Commit & Pull Request Guidelines
- Use concise, imperative commit messages (e.g., `add deferred refresh helper`). Reference change IDs when touching spec-managed work (`update-background-refresh-flow`).
- Every PR should summarize the user-visible effect, list key files touched, and note manual/automated tests executed. Attach screenshots or log excerpts for GUI or sync changes.
- Keep diffs focused: configuration secrets (e.g., `credentials.enc`) must never be committed. Update `openspec/changes/<id>/tasks.md` checkboxes once implementation is complete.

## Security & Configuration Tips
- Sensitive data lives in `config.json`/`credentials.enc`. Never hard-code tokens; read through `utils.config_manager` helpers instead.
- When sharing artifacts, strip personal paths (e.g., `E:\Workspaces\...`) or replace them with placeholders in documentation.
