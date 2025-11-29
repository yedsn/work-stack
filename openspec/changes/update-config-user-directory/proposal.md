# Change: Move configuration into per-user data directory

## Why
- Today Work Stack reads and writes config.json next to the executable, which breaks for multi-user installs and packaged builds that cannot write inside Program Files.
- Users requested that every configuration artifact live under their user profile so edits stay persistent no matter where the binary runs from.

## What Changes
- Resolve a stable per-user data root (e.g., %APPDATA%/Work Stack, ~/Library/Application Support/Work Stack, or ~/.config/work-stack) and move the primary config.json, credentials, caches, and history files there.
- Add migration logic: when the legacy project-root config.json exists copy (or move) it into the user directory on first launch and keep backups so settings are not lost.
- Update documentation, build scripts, and GUI affordances (such as the "open config" action) to reference the new location instead of the project directory.

## Impact
- Affected specs: configuration-storage
- Affected code: utils.config_manager, utils.config_history, gui/main_window.py (config shortcut), packaging/docs referencing config.json
