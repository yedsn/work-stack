# Change: Enforce single instance and focus existing window

## Why
Launching Work Stack twice currently opens a second copy, causing config contention and hotkey conflicts. Users expect relaunching the executable to simply show the existing window if it is hidden/minimized rather than spinning up another process.

## What Changes
- Detect if another Work Stack instance is already running (e.g., via OS mutex or lock file) during startup.
- When a second launch is attempted, send a message to the running instance to show/focus its window and exit the new process gracefully.
- Ensure the first instance saves enough state (e.g., window handle identifiers) to restore visibility reliably on Windows and other supported targets.
- Log events for duplicate launches to aid troubleshooting.

## Impact
- Affected specs: app-lifecycle (startup/show behavior).
- Affected code: `main.py` (entry point), `gui/main_window.py` (window focus logic), potential new helper under `utils/` for single-instance IPC, plus installer/start scripts to ensure they rely on the new behavior.
