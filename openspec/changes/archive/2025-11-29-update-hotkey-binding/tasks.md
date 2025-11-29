## 1. 热键能力定义
- [x] 1.1 根据现有代码，整理 Windows、macOS 热键注册流程与依赖，补齐缺失处理。
- [x] 1.2 在 `global-hotkey` 规格中新增/更新要求，覆盖默认组合、设置流程与跨平台行为。
- [x] 1.3 通过 `openspec validate update-hotkey-binding --strict` 确认规格无误。

## 2. 实现与验证（后续阶段）
- [x] 2.1 更新 `main.py` 与 GUI 设置以读取 `alt+w` 默认值，并允许用户覆盖。
- [x] 2.2 补齐 Windows/macOS 热键管理器，确保注册/注销、失焦恢复等流程符合规格。
- [x] 2.3 添加/更新自动化或手动验证步骤，覆盖 Windows 与 macOS 烟雾测试。（手动验证建议：① 在 Windows 上运行 `python main.py` 并使用 Alt+W 切换窗口，同时在“全局热键”菜单中禁用/启用确认即时生效；② 在 macOS 上授予辅助功能权限后执行相同流程，观察日志确认注册与注销成功。）
