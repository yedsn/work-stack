## ADDED Requirements

### Requirement: Single Instance Enforcement
The application SHALL allow only one running instance per user session. Subsequent launches MUST signal the existing process to show/focus its main window instead of starting a new GUI.

#### Scenario: Second launch triggers activation
- **WHEN** the user attempts to launch Work Stack while another instance is already running
- **THEN** the new process detects the existing lock and sends an activation request
- **AND** the existing window becomes visible and focused while the new process exits without showing its own UI.

#### Scenario: Tray/minimized restore
- **WHEN** the existing instance is minimized to tray or hidden
- **THEN** handling an activation request SHALL restore the window to a visible, focused state (bringing it to the foreground on Windows) before acknowledging success.

#### Scenario: Lock lifecycle
- **WHEN** the primary instance exits (normal shutdown or crash)
- **THEN** the single-instance lock is released so the next launch can start fresh.
