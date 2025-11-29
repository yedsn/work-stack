## 1. Implementation
- [x] 1.1 Identify every module that reads or writes config artifacts (config.json, credentials.enc, config_history) and document the current assumptions. (Touched modules: `utils.config_manager`, `utils.config_history`, `utils.config_cleanup`, `utils.credential_manager`, `gui/main_window.py`, `cli.py`, `build_exe.py`, README/docs references.)
- [x] 1.2 Add a path helper that resolves a per-user application data directory on Windows/macOS/Linux and exposes file paths for config, credentials, and history.
- [x] 1.3 Update config loading/saving, history retention, and any file watchers to use the new helper plus automatic migration from the legacy project-root files.
- [x] 1.4 Adjust GUI affordances, packaging scripts, and docs that instruct users to edit config.json so they reference the new user-directory path, including guidance for PyInstaller builds.
- [x] 1.5 Add regression coverage (unit or integration) proving that missing user-directory configs fall back to defaults, that migration copies an existing project-root config exactly once, and that the helper picks OS-specific folders.
