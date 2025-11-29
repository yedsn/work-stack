#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu, QMenuBar, QAction, QShortcut
from PyQt5.QtGui import QIcon, QFont, QPixmap, QKeySequence, QCursor
from PyQt5.QtCore import QSize, Qt, QTimer
from gui.main_window import LaunchGUI
from utils.logger import get_logger
from utils.single_instance import SingleInstanceManager
from utils.path_utils import resource_path
from utils.config_manager import (
    load_config,
    ensure_hotkey_defaults,
    DEFAULT_TOGGLE_HOTKEY,
)

# 获取日志记录器
logger = get_logger("launcher")

_singleton_window = None


def bring_existing_window_to_front():
    """Handle activation from a duplicate process."""
    global _singleton_window
    app = QApplication.instance()
    if not app:
        logger.warning("收到激活请求但应用尚未初始化")
        return
    if not _singleton_window:
        logger.warning("收到激活请求但主窗口未就绪")
        return
    logger.info("收到激活请求，恢复窗口")
    QTimer.singleShot(0, _singleton_window.show_normal_and_raise)


def main():
    global _singleton_window
    # 记录应用启动
    logger.info("应用启动器开始启动")
    instance_manager = SingleInstanceManager()
    has_lock = instance_manager.acquire(bring_existing_window_to_front)
    if not has_lock:
        logger.info("检测到已有运行实例，尝试激活已启动的窗口")
        if instance_manager.activate_existing():
            logger.info("已请求激活现有窗口，退出重复进程")
            return 0
        logger.error("已存在实例但无法激活，退出以避免多开")
        return 1

    hotkey_manager = None

    # Windows 高 DPI 支持设置
    if sys.platform == 'win32':
        # 确保在高 DPI 显示器上文字不会太小
        # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        # 设置默认字体大小
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        logger.debug("已设置 Windows DPI 感知")
    
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = resource_path("resources", "icon.png")
    if not os.path.exists(icon_path):
        logger.warning(f"图标文件 {icon_path} 不存在")
        # 在Mac上，创建一个空图标也比没有图标好
        if sys.platform == 'darwin':
            empty_icon = QPixmap(64, 64)
            empty_icon.fill(Qt.transparent)
            app.setWindowIcon(QIcon(empty_icon))
    else:
        app.setWindowIcon(QIcon(icon_path))
        logger.debug("已设置应用图标")
    
    # Windows 特定设置
    if sys.platform == 'win32':
        # 设置全局字体大小
        font = QFont()
        font.setPointSize(10)  # 设置默认字体大小
        app.setFont(font)
        logger.debug("已应用 Windows 特定设置")
    
    # Mac OS X 特定设置
    if sys.platform == 'darwin':
        try:
            # 设置 macOS Dock 栏图标
            app.setAttribute(Qt.AA_DontShowIconsInMenus, False)
            
            # 设置应用名称 (在 macOS 的菜单栏中显示)
            app.setApplicationName("应用启动器")
            
            # 设置 macOS 的外观
            os.environ['QT_MAC_WANTS_LAYER'] = '1'
            
            # 设置高DPI缩放
            app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
            # 添加应用程序激活事件处理 - 点击程序坞图标时显示窗口
            def applicationStateChanged(state):
                # 当应用程序变为活动状态但窗口不可见时，显示窗口
                if state == Qt.ApplicationActive and not window.isVisible():
                    window.show()
                    window.raise_()
                    window.activateWindow()
                    logger.debug("通过应用程序状态变化显示窗口")
            
            # macOS 菜单栏设置
            main_menu = QMenuBar()
            
            # 创建文件菜单
            file_menu = QMenu("文件")
            file_menu.addAction("导入配置")
            file_menu.addAction("导出配置")
            file_menu.addSeparator()
            exit_action = QAction("退出", app)
            exit_action.triggered.connect(app.quit)
            file_menu.addAction(exit_action)
            
            main_menu.addMenu(file_menu)
            
            # 添加帮助菜单
            help_menu = QMenu("帮助")
            about_action = QAction("关于", app)
            about_action.triggered.connect(lambda: show_about_dialog())
            help_menu.addAction(about_action)
            
            main_menu.addMenu(help_menu)
            
            # 设置菜单栏
            app.setMenuBar(main_menu)
            logger.debug("已应用 macOS 特定设置")
            
        except Exception as e:
            logger.error(f"设置 macOS 特定特性时发生错误: {e}")
    
    # 关于对话框
    def show_about_dialog():
        QMessageBox.about(None, "关于应用启动器", 
                         "应用启动器 v1.0\n\n"
                         "一个便捷的应用程序和网站启动工具，\n"
                         "支持 Windows 和 Mac 系统优化。\n\n"
                         "© 2023 YourCompany")
        logger.debug("显示关于对话框")
    
    window = LaunchGUI()
    _singleton_window = window
    logger.info("主窗口已创建")
    
    # 添加键盘快捷键
    # Esc 键隐藏窗口
    hide_shortcut = QShortcut(QKeySequence("Esc"), window)
    hide_shortcut.activated.connect(window.hide_and_clear_search)
    
    # 构建为热键切换准备的设置对象
    def build_hotkey_settings():
        class Settings:
            pass

        settings = Settings()

        def show_window_from_hotkey():
            try:
                if hasattr(window, "show_normal_and_raise"):
                    window.show_normal_and_raise()
                else:
                    window.show()
                    window.raise_()
                    window.activateWindow()
                logger.debug("通过全局热键显示窗口")
            except Exception as err:
                logger.error(f"显示窗口时出错: {err}")

        def hide_window_from_hotkey():
            try:
                if hasattr(window, "hide_and_clear_search"):
                    window.hide_and_clear_search()
                else:
                    window.hide()
                logger.debug("通过全局热键隐藏窗口")
            except Exception as err:
                logger.error(f"隐藏窗口时出错: {err}")

        settings.show_window = show_window_from_hotkey
        settings.minimize_to_tray = hide_window_from_hotkey
        return settings

    # 设置全局快捷键
    if sys.platform == 'win32':
        try:
            from gui.hotkey_manager_win import HotkeyManagerWin

            config = ensure_hotkey_defaults(load_config(), persist=True)

            settings = build_hotkey_settings()
            settings.toggle_hotkey = config.get("toggle_hotkey", DEFAULT_TOGGLE_HOTKEY)

            enable_hotkey = config.get("enable_hotkey", True)
            hotkey_manager = HotkeyManagerWin(window, settings)
            window.set_hotkey_manager(hotkey_manager)

            if enable_hotkey:
                hotkey_manager.register_hotkey(settings.toggle_hotkey)
                logger.info(f"已注册全局热键: {settings.toggle_hotkey}")
            else:
                logger.info("全局热键已禁用")

        except Exception as e:
            logger.error(f"初始化热键管理器失败: {e}")
            show_shortcut = QShortcut(QKeySequence("alt+`"), window)
            show_shortcut.activated.connect(lambda: (window.show(), window.activateWindow()))
            logger.debug("已设置应用内快捷键 (热键管理器初始化失败)")
    elif sys.platform == 'darwin':
        try:
            from gui.hotkey_manager_mac import HotkeyManagerMac

            config = ensure_hotkey_defaults(load_config(), persist=True)
            settings = build_hotkey_settings()
            settings.toggle_hotkey = config.get("toggle_hotkey", DEFAULT_TOGGLE_HOTKEY)
            enable_hotkey = config.get("enable_hotkey", True)

            hotkey_manager = HotkeyManagerMac(window, settings)
            window.set_hotkey_manager(hotkey_manager)

            if enable_hotkey:
                success = hotkey_manager.register_hotkey(settings.toggle_hotkey)
                if success:
                    logger.info(f"已注册 macOS 全局热键: {settings.toggle_hotkey}")
                else:
                    logger.warning("macOS 全局热键注册失败，启用应用内快捷键作为回退")
                    show_shortcut = QShortcut(QKeySequence("alt+`"), window)
                    show_shortcut.activated.connect(lambda: (window.show(), window.activateWindow()))
            else:
                logger.info("macOS 全局热键已禁用")

        except Exception as e:
            logger.error(f"初始化 macOS 热键管理器失败: {e}")
            show_shortcut = QShortcut(QKeySequence("alt+`"), window)
            show_shortcut.activated.connect(lambda: (window.show(), window.activateWindow()))
            logger.debug("已设置应用内快捷键 (macOS)")
    else:  # Linux 平台
        try:
            # 导入 Linux 平台的热键管理器
            from gui.hotkey_manager_linux import HotkeyManagerLinux
            
            # TODO: 实现 Linux 平台的热键注册
            logger.warning("Linux 平台的全局热键功能尚未实现")
            
            # 使用普通快捷键
            show_shortcut = QShortcut(QKeySequence("alt+`"), window)
            show_shortcut.activated.connect(lambda: (window.show(), window.activateWindow()))
            logger.debug("已设置应用内快捷键 (Linux)")
            
        except Exception as e:
            logger.error(f"初始化 Linux 热键管理器失败: {e}")
    
    if hotkey_manager:
        def cleanup_hotkeys():
            try:
                hotkey_manager.unregister_hotkey()
                logger.debug("已清理全局热键")
            except Exception as e:
                logger.error(f"清理全局热键时出错: {e}")

        app.aboutToQuit.connect(cleanup_hotkeys)

    # 创建系统托盘图标
    icon = QIcon(icon_path) if os.path.exists(icon_path) else app.windowIcon()
    tray_icon = QSystemTrayIcon(icon, app)
    tray_menu = QMenu()
    
    # 添加托盘菜单项
    show_action = tray_menu.addAction("显示窗口")
    show_action.triggered.connect(window.show)
    
    hide_action = tray_menu.addAction("隐藏窗口")
    hide_action.triggered.connect(window.hide)
    
    tray_menu.addSeparator()
    
    quit_action = tray_menu.addAction("退出应用")
    quit_action.triggered.connect(app.quit)
    
    # 设置托盘菜单
    if sys.platform == 'darwin':
        def show_context_menu(reason):
            if reason == QSystemTrayIcon.Context: 
                pos = QCursor.pos()
                # 显示上下文菜单
                tray_menu.exec_(pos)
        
        # 连接托盘图标的激活信号到我们的自定义处理函数
        tray_icon.activated.connect(show_context_menu)
    else:
        tray_icon.setContextMenu(tray_menu)
    
    # 添加托盘图标的左键点击事件处理
    def tray_icon_activated(reason):
        # 根据不同平台处理点击事件
        if sys.platform == 'win32':
            # 在Windows上，单击为ActivationReason.Trigger (1)
            if reason == QSystemTrayIcon.Trigger:
                if window.isVisible():
                    window.hide()
                    logger.debug("通过托盘图标隐藏窗口")
                else:
                    window.show()
                    window.activateWindow()  # 确保窗口获得焦点
                    logger.debug("通过托盘图标显示窗口")
        elif sys.platform == 'darwin':
            # 在macOS上，单击也显示窗口
            if reason == QSystemTrayIcon.Trigger:
                window.show()
                window.raise_()  # 将窗口提升到顶层
                window.activateWindow()  # 确保窗口获得焦点
                logger.debug("通过托盘图标显示窗口 (macOS)")
                # 使用AppKit将应用程序带到前台
                import AppKit
                AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    
    # 连接托盘图标的激活信号
    tray_icon.activated.connect(tray_icon_activated)
    
    # 显示托盘图标
    tray_icon.show()
    logger.debug("系统托盘图标已显示")
    
    # 将托盘图标传递给主窗口，便于管理
    window.set_tray_icon(tray_icon)
    
    # 显示主窗口
    window.show()
    logger.info("主窗口已显示")
    
    # 连接应用程序状态变化信号（macOS特定）
    if sys.platform == 'darwin':
        app.applicationStateChanged.connect(applicationStateChanged)

    # 设置应用退出时的清理函数
    def cleanup_on_exit():
        global _singleton_window
        try:
            from utils.config_manager import flush_config
            # 刷新所有未保存的配置
            flush_config()

            # 清理主窗口资源
            if window:
                window.cleanup_resources()

            # 清理热键管理器
            if hotkey_manager:
                hotkey_manager.cleanup()

            _singleton_window = None
            logger.info("应用退出清理完成")
        except Exception as e:
            logger.error(f"应用退出清理失败: {e}")
    
    import atexit
    atexit.register(cleanup_on_exit)
    
    logger.info("应用程序进入主循环")
    try:
        exit_code = app.exec_()
    finally:
        # 确保清理
        cleanup_on_exit()
        if has_lock:
            instance_manager.release()
    
    logger.info(f"应用程序退出，退出代码: {exit_code}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 
