#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu, QMenuBar, QAction, QShortcut
from PyQt5.QtGui import QIcon, QFont, QPixmap, QKeySequence, QCursor
from PyQt5.QtCore import QSize, Qt, QTimer
from gui.main_window import LaunchGUI
from utils.logger import get_logger

# 获取日志记录器
logger = get_logger("launcher")

# 导入全局快捷键库
try:
    import keyboard
    has_keyboard_lib = True
except ImportError:
    has_keyboard_lib = False
    logger.warning("未能导入keyboard库，全局热键功能将不可用")

def main():
    # 记录应用启动
    logger.info("应用启动器开始启动")
    
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
    icon_path = "resources/icon.png"
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
    logger.info("主窗口已创建")
    
    # 添加键盘快捷键
    # Esc 键隐藏窗口
    hide_shortcut = QShortcut(QKeySequence("Esc"), window)
    hide_shortcut.activated.connect(window.hide_and_clear_search)
    
    # 设置全局快捷键
    if sys.platform == 'win32':
        try:
            # 导入 Windows 平台的热键管理器
            from gui.hotkey_manager_win import HotkeyManagerWin
            
            from utils.config_manager import load_config
            config = load_config()
            
            # 创建一个简单的设置对象
            class Settings:
                pass
                
            settings = Settings()
            
            # 设置热键
            if not hasattr(settings, 'toggle_hotkey'):
                # 从配置文件中读取热键设置
                settings.toggle_hotkey = config.get('toggle_hotkey', 'ctrl+shift+z')
                
            def minimize_to_tray():
                try:
                    window.withdraw()
                    logger.debug("通过全局热键隐藏窗口")
                except Exception as e:
                    logger.error(f"隐藏窗口时出错: {e}")
                    
            # 将这些方法添加到settings对象
            settings.show_window = window.show
            settings.minimize_to_tray = minimize_to_tray
                
            # 检查是否启用全局热键
            enable_hotkey = config.get('enable_hotkey', True)
            
            if enable_hotkey:
                # 创建热键管理器实例
                hotkey_manager = HotkeyManagerWin(window, settings)
                
                # 设置窗口对热键管理器的引用
                window.set_hotkey_manager(hotkey_manager)
                
                # 注册热键
                hotkey_manager.register_hotkey()
                logger.info(f"已注册全局热键: {settings.toggle_hotkey}")
            else:
                logger.info("全局热键已禁用")
            
            # 确保应用退出时清理热键
            def cleanup_hotkeys():
                try:
                    hotkey_manager.unregister_hotkey()
                    logger.debug("已清理全局热键")
                except Exception as e:
                    logger.error(f"清理全局热键时出错: {e}")
            
            app.aboutToQuit.connect(cleanup_hotkeys)
            
        except Exception as e:
            logger.error(f"初始化热键管理器失败: {e}")
            # 如果热键管理器初始化失败，使用普通快捷键
            show_shortcut = QShortcut(QKeySequence("alt+`"), window)
            show_shortcut.activated.connect(lambda: (window.show(), window.activateWindow()))
            logger.debug("已设置应用内快捷键 (热键管理器初始化失败)")
    elif sys.platform == 'darwin':
        try:
            # 导入 macOS 平台的热键管理器
            from gui.hotkey_manager_mac import HotkeyManagerMac
            
            # TODO: 实现 macOS 平台的热键注册
            logger.warning("macOS 平台的全局热键功能尚未实现")
            
            # 使用普通快捷键
            show_shortcut = QShortcut(QKeySequence("alt+`"), window)
            show_shortcut.activated.connect(lambda: (window.show(), window.activateWindow()))
            logger.debug("已设置应用内快捷键 (macOS)")
            
        except Exception as e:
            logger.error(f"初始化 macOS 热键管理器失败: {e}")
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
        try:
            from utils.config_manager import flush_config
            # 刷新所有未保存的配置
            flush_config()
            
            # 清理主窗口资源
            if 'window' in locals():
                window.cleanup_resources()
            
            # 清理热键管理器
            if 'hotkey_manager' in locals() and hotkey_manager:
                hotkey_manager.cleanup()
                
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
    
    logger.info(f"应用程序退出，退出代码: {exit_code}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 