#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import webbrowser
import time
import threading
import platform
from typing import List, Dict, Any, Optional, Union

from utils.os_utils import get_os_type, expand_path
from utils.ui_utils import print_colored

def open_browser(browser_name: str, urls: List[str], window_name: Optional[str] = None) -> None:
    """
    打开指定浏览器并访问提供的URL列表
    
    Args:
        browser_name: 浏览器名称 (chrome, edge, firefox, safari)
        urls: 要打开的URL列表
        window_name: 可选的窗口名称（已弃用，保留参数以兼容现有配置）
    """
    os_type = get_os_type()
    browser_paths = {
        "windows": {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
        },
        "mac": {
            "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
            "safari": "/Applications/Safari.app/Contents/MacOS/Safari"
        },
        "linux": {
            "chrome": "google-chrome",
            "edge": "microsoft-edge",
            "firefox": "firefox",
        }
    }
    
    browser_cmd = browser_paths.get(os_type, {}).get(browser_name.lower())
    
    if not browser_cmd:
        print_colored(f"未找到浏览器: {browser_name}，尝试使用系统默认浏览器", "yellow")
        for url in urls:
            webbrowser.open(url)
        return
    
    # 构建命令行参数
    cmd = [browser_cmd]
    
    # 始终使用新窗口
    if browser_name.lower() in ["chrome", "edge"]:
        cmd.append("--new-window")
    elif browser_name.lower() == "firefox":
        cmd.append("-new-window")
    
    # 添加URL
    cmd.extend(urls)
    
    print_colored(f"执行命令: {cmd}", "blue")
    
    try:
        subprocess.Popen(cmd)
        # 给浏览器一些启动时间
        time.sleep(1)
    except Exception as e:
        print_colored(f"启动浏览器时出错: {e}", "red")
        print_colored("尝试使用系统默认浏览器", "yellow")
        for url in urls:
            webbrowser.open(url)

def open_vscode(project_path: str) -> None:
    """
    打开VSCode并加载指定项目
    
    Args:
        project_path: 项目路径
    """
    os_type = get_os_type()
    
    vscode_paths = {
        "windows": "C:/Program Files/Microsoft VS Code/Code.exe",  # Windows通常将VSCode添加到PATH
        "mac": "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
        "linux": "code"  # Linux通常将VSCode添加到PATH
    }
    
    vscode_cmd = vscode_paths.get(os_type)
    
    if not vscode_cmd:
        print_colored("未找到VSCode", "red")
        return
    
    # 展开用户目录（如 ~/projects）
    expanded_path = expand_path(project_path)
    
    try:
        subprocess.Popen([vscode_cmd, expanded_path])
    except Exception as e:
        print_colored(f"启动VSCode时出错: {e}", "red")

def open_app(app_name: str, params: Union[List[str], str] = None) -> None:
    """
    打开指定的应用程序
    
    Args:
        app_name: 应用程序名称
        params: 应用程序参数，可以是字符串或字符串列表
    """
    if params is None:
        params = []
    
    # 如果params是字符串，转换为列表
    if isinstance(params, str):
        params = [params]
        
    os_type = get_os_type()
    
    # 特殊处理常见应用
    if app_name.lower() == "chrome":
        open_browser("chrome", params)
        return
    elif app_name.lower() in ["edge", "msedge"]:
        open_browser("edge", params)
        return
    elif app_name.lower() == "firefox":
        open_browser("firefox", params)
        return
    elif app_name.lower() == "safari":
        open_browser("safari", params)
        return
    elif app_name.lower() in ["vscode", "code"]:
        if params and len(params) > 0:
            open_vscode(params[0])
        else:
            open_vscode("")
        return
    
    # 通用应用启动
    if os_type == "mac":
        cmd = ["open", "-a", app_name]
        if params:
            cmd.append("--args")
            cmd.extend(params)
    elif os_type == "windows":
        cmd = [app_name]
        if params:
            cmd.extend(params)
    else:  # Linux
        cmd = [app_name]
        if params:
            cmd.extend(params)
    
    try:
        print_colored(f"执行命令: {cmd}", "blue")
        subprocess.Popen(cmd)
    except Exception as e:
        print_colored(f"启动应用程序时出错: {e}", "red")

def launch_program(program: Dict[str, Any], config_dir: str) -> None:
    """
    根据配置启动程序
    
    Args:
        program: 程序配置字典
        config_dir: 配置文件所在目录
    """
    print_colored(f"\n▶ 正在启动: {program['name']}", "cyan")
    
    # 处理新的launch_items格式
    if "launch_items" in program:
        for item in program["launch_items"]:
            app = item.get("app")
            params = item.get("params")
            
            if app:
                print_colored(f"  → 启动应用: {app}", "yellow")
                open_app(app, params)
    # 处理直接传递的简单配置
    elif "app" in program:
        app = program.get("app")
        params = program.get("params", [])
        
        print_colored(f"  → 启动应用: {app}", "yellow")
        print_colored(f"  → 参数: {params}", "yellow")
        open_app(app, params)
    # 兼容旧格式
    elif "config_file" in program:
        config_file = program["config_file"]
        config_path = os.path.join(config_dir, config_file)
        
        if not os.path.exists(config_path):
            print_colored(f"错误: 程序配置文件 '{config_path}' 不存在", "red")
            return
            
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                program_data = json.load(f)
                print_colored(f"已加载配置: {json.dumps(program_data, ensure_ascii=False, indent=2)}", "blue")
                # 处理旧格式的配置
                # 这里可以添加处理旧格式配置的代码
        except Exception as e:
            print_colored(f"处理配置文件时出错: {e}", "red")
    else:
        print_colored(f"错误: 无法识别的程序配置格式: {program}", "red")
