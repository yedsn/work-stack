#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess

def build_exe():
    print("开始打包应用程序...")
    
    # 确定主脚本路径
    main_script = "main.py"
    if not os.path.exists(main_script):
        print(f"错误：找不到主脚本 {main_script}")
        return False
    
    # 创建输出目录
    output_dir = "dist"
    if os.path.exists(output_dir):
        print(f"清理旧的输出目录: {output_dir}")
        shutil.rmtree(output_dir)
    
    # 检查图标文件是否存在
    icon_path = "resources/icon.ico"
    if not os.path.exists(icon_path):
        print(f"警告：图标文件 {icon_path} 不存在，将使用默认图标")
        icon_option = []  # 不指定图标选项
    else:
        icon_option = [f"--icon={icon_path}"]
    
    # 检查资源目录是否存在
    resources_path = "resources"
    if not os.path.exists(resources_path):
        print(f"警告：资源目录 {resources_path} 不存在")
        resources_option = []
    else:
        resources_option = [f"--add-data={resources_path};{resources_path}"]
    
    # 检查配置文件是否存在
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"警告：配置文件 {config_path} 不存在")
        config_option = []
    else:
        config_option = [f"--add-data={config_path};."]
    
    # 构建 PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--name=应用启动器",
        "--windowed",  # 使用 GUI 模式，不显示控制台
        "--noconfirm",  # 不询问确认
        "--clean",  # 清理临时文件
    ]
    
    # 添加可选参数
    cmd.extend(icon_option)
    cmd.extend(resources_option)
    cmd.extend(config_option)
    
    # 添加主脚本
    cmd.append(main_script)
    
    # 执行打包命令
    print("执行打包命令:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        print("打包完成！")
        print(f"可执行文件位于: {os.path.join(output_dir, '应用启动器.exe')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        return False

if __name__ == "__main__":
    build_exe() 