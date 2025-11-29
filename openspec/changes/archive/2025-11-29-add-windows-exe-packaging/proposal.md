# Change: Add Windows EXE Packaging

## Why
Windows users need a one-step way to turn the PyQt launcher into a standalone executable so it can be distributed without asking teammates to install Python or dependencies. Today the repo only ships source code and an ad hoc script without any guarantees, so packaging success is inconsistent.

## What Changes
- Provide an official PyInstaller-driven packaging flow that builds a signed (or sign-ready) EXE from `main.py`.
- Bundle required resources (icons, config templates, JSON assets) and ensure secrets never leak into the artifact.
- Add automation/docs so developers can run `python build_exe.py` locally and confirm the binary launches.

## Impact
- Affected specs: `distribution/windows-exe`
- Affected code: `build_exe.py`, `README.md`, optional CI helpers or scripts under `scripts/`.

