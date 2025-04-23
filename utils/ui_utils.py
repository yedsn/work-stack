#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Dict, Any

def print_colored(text: str, color: str = None) -> None:
    """打印彩色文本"""
    colors = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'underline': '\033[4m'
    }
    
    if color and color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text)

def display_menu_multi(programs: List[Dict[str, Any]]) -> List[int]:
    """显示程序菜单并支持多选"""
    print("\n")
    print_colored("╔═════════════════════════════════════╗", "cyan")
    print_colored("║           程序启动器               ║", "cyan")
    print_colored("╚═════════════════════════════════════╝", "cyan")
    print("\n可用程序列表:")
    
    for idx, program in enumerate(programs, 1):
        print_colored(f"  {idx}. {program['name']} - {program['description']}", "green")
    
    print("\n" + "─" * 50)
    print_colored("命令说明:", "yellow")
    print("  数字: 选择单个程序")
    print("  多个数字(用空格分隔): 同时选择多个程序 (例如: 1 3)")
    print("  a: 选择所有程序")
    print("  q: 退出程序")
    print("─" * 50 + "\n")
    
    while True:
        choice = input("> 请输入您的选择: ").strip().lower()
        
        if choice == 'q':
            return []
        
        if choice == 'a':
            return list(range(1, len(programs) + 1))
        
        try:
            # 处理多选
            if ' ' in choice:
                selections = [int(x) for x in choice.split()]
                # 验证所有选择是否有效
                if all(1 <= s <= len(programs) for s in selections):
                    return selections
                else:
                    print_colored("错误: 选择范围应在 1 到 {} 之间".format(len(programs)), "red")
            else:
                # 处理单选
                selection = int(choice)
                if 1 <= selection <= len(programs):
                    return [selection]
                else:
                    print_colored("错误: 选择范围应在 1 到 {} 之间".format(len(programs)), "red")
        except ValueError:
            print_colored("错误: 请输入有效的数字或命令", "red") 