## 1. Packaging workflow
- [x] 1.1 Update `build_exe.py` to invoke PyInstaller with Windows-safe flags, embed version metadata, and copy required resources/config templates without secrets.
- [x] 1.2 Ensure the script surfaces friendly errors (missing PyInstaller, missing icon) and documents prerequisites inside the module docstring.

## 2. Documentation & verification
- [x] 2.1 Add README instructions covering environment setup, command invocation, and troubleshooting for the EXE workflow.
- [x] 2.2 Run `python build_exe.py` on Windows to verify the artifact launches `main.py` without a console window; capture the resulting EXE path in the change log or release notes.
- [x] 2.3 Attach the local packaging run output (or screenshots/log excerpts) when requesting review to prove validation succeeded.

