# Change: 更新热键绑定并统一默认值

## Why
当前全局热键依赖平台各自的实现，未形成明确要求，且默认组合仍是 `ctrl+shift+z`。需要确保 Windows 与 macOS 均能稳定注册热键，并把默认组合调整为更便于单手触发的 `alt+w`。

## What Changes
- 定义“全局热键”能力的行为与状态管理，包括 Windows、macOS 的注册和回调。
- 规定默认热键组合为 `alt+w`，应用启动时应自动使用（除非用户覆盖配置）。
- 记录在 GUI 设置中切换、重设热键时的配置流转，以便后续实现和测试。

## Impact
- Affected specs: `global-hotkey`
- Affected code: `main.py`, `gui/hotkey_manager_win.py`, `gui/hotkey_manager_mac.py`, `gui/main_window.py`, `utils/config_manager.py`（如需）
