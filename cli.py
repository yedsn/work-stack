#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from typing import List, Dict, Any

from utils.ui_utils import print_colored, display_menu_multi
from utils.app_launcher import launch_program
from utils.config_manager import load_config, get_programs
from utils.path_utils import get_user_config_path

def main():
    # 检查参数数量
    if len(sys.argv) == 1:
        # 没有参数时，加载默认配置并显示程序列表
        try:
            # 加载配置（config_manager会自动处理路径）
            config = load_config()
            programs = get_programs(config)
            
            if not programs:
                sys.exit(1)
                
            # 显示菜单并获取用户选择
            choices = display_menu_multi(programs)
            
            if not choices:
                print_colored("退出程序", "yellow")
                sys.exit(0)
            
            # 获取配置文件所在目录
            config_dir = str(get_user_config_path().parent)
            
            # 启动所有选中的程序
            for choice in choices:
                selected_program = programs[choice-1]
                launch_program(selected_program, config_dir)
            
            print_colored("\n✓ 所有选定的程序已启动", "green")
            return
            
        except json.JSONDecodeError:
            print_colored(f"错误: 配置文件 '{config_file}' 格式不正确", "red")
            sys.exit(1)
        except Exception as e:
            print_colored(f"发生错误: {str(e)}", "red")
            sys.exit(1)
    
    # 直接启动模式：接收程序名、应用和参数
    if len(sys.argv) >= 3:
        program_name = sys.argv[1]
        app_name = sys.argv[2]
        
        # 收集所有剩余参数
        params = []
        if len(sys.argv) > 3:
            params = sys.argv[3:]
        
        # 打印调试信息
        print_colored(f"调试信息: 程序名={program_name}, 应用={app_name}, 参数={params}", "blue")
        
        # 创建程序配置
        program = {
            "name": program_name,
            "app": app_name,
            "params": params
        }
        
        # 获取当前工作目录
        working_dir = os.getcwd()
        
        # 启动程序
        print_colored(f"▶ 正在启动: {program_name}", "cyan")
        try:
            launch_program(program, working_dir)
            print_colored(f"\n✓ 程序 '{program_name}' 已启动", "green")
        except Exception as e:
            print_colored(f"启动程序时出错: {str(e)}", "red")
            import traceback
            print_colored(traceback.format_exc(), "red")
        return
        
    # 配置文件模式
    config_file = sys.argv[1]
    if not os.path.exists(config_file):
        print_colored(f"错误: 配置文件 '{config_file}' 不存在", "red")
        sys.exit(1)
    
    try:
        # 加载配置
        config = load_config(config_file)
        programs = get_programs(config)
        
        if not programs:
            sys.exit(1)
            
        # 显示菜单并获取用户选择
        choices = display_menu_multi(programs)
        
        if not choices:
            print_colored("退出程序", "yellow")
            sys.exit(0)
        
        # 获取配置文件所在目录
        config_dir = os.path.dirname(os.path.abspath(config_file))
        
        # 启动所有选中的程序
        for choice in choices:
            selected_program = programs[choice-1]
            launch_program(selected_program, config_dir)
        
        print_colored("\n✓ 所有选定的程序已启动", "green")
        
    except json.JSONDecodeError:
        print_colored(f"错误: 配置文件 '{config_file}' 格式不正确", "red")
        sys.exit(1)
    except Exception as e:
        print_colored(f"发生错误: {str(e)}", "red")
        sys.exit(1)

if __name__ == "__main__":
    main() 
