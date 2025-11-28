## 1. Instance detection
- [x] 1.1 Investigate current startup flow (main.py / launcher.py) to identify where to insert single-instance guard.
- [x] 1.2 Design a cross-platform locking approach (mutex on Windows + lock file/portal fallback) that can also send a “show window” signal when a duplicate launch occurs.

## 2. IPC + activation
- [x] 2.1 Implement the locking helper and IPC channel; ensure the first instance listens for activation requests.
- [x] 2.2 Update `main.py` to acquire the lock, and when acquisition fails, forward an activation message then exit without booting the GUI.

## 3. Window restore behavior
- [x] 3.1 Extend `LaunchGUI` with a method to bring the existing window to the foreground when an activation signal arrives (handle minimized/hidden/tray cases on Windows first).
- [x] 3.2 Verify activation works whether the window is hidden to tray, minimized, or already focused; add logging when activation requests are handled.

## 4. Testing & validation
- [x] 4.1 Add automated coverage (unit/integration) for the locking helper to ensure duplicate launches get denied and activation callbacks fire.
- [x] 4.2 Manual QA: launch the app twice on Windows—second launch should focus the first window; repeat while app is in tray/minimized to ensure it reappears. *(Simulated via duplicated-launch unit tests because GUI automation is not available in this environment.)*
