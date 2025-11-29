# distribution Specification

## Purpose
TBD - created by archiving change add-windows-exe-packaging. Update Purpose after archive.
## Requirements
### Requirement: Windows EXE packaging
Work Stack SHALL offer a documented PyInstaller workflow that creates a GUI-only Windows executable from `main.py`, bundles the assets the launcher needs on first run, and blocks releases that would leak secrets or omit resources.

#### Scenario: Packaging succeeds on Windows
- **GIVEN** a developer on Windows has Python, dependencies, and PyInstaller installed
- **WHEN** they run `python build_exe.py`
- **THEN** the script builds a console-free executable under `dist/` whose name matches the product branding
- **AND** the binary launches the same UI as `python main.py` while loading bundled resources and template configs
- **AND** the script surfaces actionable errors if PyInstaller or required assets are missing so packaging cannot silently produce a broken artifact

#### Scenario: Artifact contains required assets
- **WHEN** the EXE build finishes
- **THEN** icon files, resource directories, and sanitized config templates are included in the bundle so the launcher starts with branding intact and without shipping secrets

