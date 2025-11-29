## ADDED Requirements
### Requirement: User directory configuration storage
Work Stack SHALL store config.json, related credentials, and config history exclusively inside a per-user application data directory (%APPDATA%/Work Stack on Windows, ~/Library/Application Support/Work Stack on macOS, and ~/.config/work-stack on Linux) so builds remain writable regardless of where the binary lives.

#### Scenario: Primary config loads from user directory
- **GIVEN** a supported desktop OS and the application launches from any install location (git checkout, Program Files, or a PyInstaller bundle)
- **THEN** the app creates the per-user directory if missing and reads/writes config.json, credentials, and config_history only within that folder

#### Scenario: Legacy project-root configs migrate automatically
- **GIVEN** an existing config.json or config_history under the legacy project root
- **WHEN** a newer build starts after introducing the per-user directory
- **THEN** the app copies the legacy files into the user directory exactly once, leaves a timestamped backup in case rollback is needed, and switches to the new location without re-reading the legacy files afterward

#### Scenario: GUI affordances expose the new location
- **WHEN** a user invokes UI actions or documentation instructions that open or edit the config
- **THEN** the surfaces reference and open the per-user directory path so the workflow matches where the file actually lives
