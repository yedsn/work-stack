# global-hotkey Specification

## Purpose
TBD - created by archiving change update-hotkey-binding. Update Purpose after archive.
## Requirements
### Requirement: Global Hotkey Toggle
The launcher SHALL provide a single global hotkey that toggles the main window visibility while leaving background sync untouched. The binding MUST be supported on Windows (using the native keyboard hook) and macOS (via Carbon/Quartz APIs or provided fallbacks). The GUI MUST allow the user to enable/disable the binding and re-register it without restarting the app.

#### Scenario: Windows toggle
- **GIVEN** Windows 10+ with the launcher running and global hotkeys enabled
- **WHEN** the configured hotkey combination is pressed
- **THEN** the launcher SHALL either show the window if hidden/minimized or hide it if visible, and a log entry SHALL confirm the hotkey fired.

#### Scenario: macOS toggle
- **GIVEN** macOS (Intel �� Apple Silicon) with accessibility permission granted and global hotkeys enabled
- **WHEN** the configured hotkey combination is pressed
- **THEN** the launcher SHALL toggle the main window visibility without freezing the menu bar icon, and a debug log SHALL confirm the callback executed.

#### Scenario: Enable/disable via settings
- **GIVEN** a user opens the ��ȫ���ȼ������ò˵�
- **WHEN** they toggle the enablement checkbox
- **THEN** the launcher SHALL register or unregister the current hotkey immediately and persist `enable_hotkey` to config.

### Requirement: Global Hotkey Defaults
The launcher SHALL default the toggle combination to `alt+w` (?+W on macOS) on first launch or when no `toggle_hotkey` is set. Any manual change SHALL be persisted and used across restarts.

#### Scenario: Default initialization
- **GIVEN** the config lacks `toggle_hotkey`
- **WHEN** the launcher initializes settings
- **THEN** it SHALL set `toggle_hotkey` to `alt+w` and register that binding.

#### Scenario: User override persists
- **GIVEN** a user replaces the hotkey via the settings dialog with a valid combination
- **WHEN** the app restarts
- **THEN** the launcher SHALL keep the user-defined value and register it instead of falling back to `alt+w`.

