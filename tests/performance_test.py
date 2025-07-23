#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import psutil
import threading
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.config_manager import load_config, save_config, clear_config_cache
from gui.main_window import LaunchGUI

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()
        self.measurements = []
        self.monitoring = False
        
    def start_monitoring(self, duration=10):
        """开始监控指定时间（秒）"""
        self.monitoring = True
        self.measurements = []
        
        def monitor():
            start_time = time.time()
            while self.monitoring and (time.time() - start_time) < duration:
                try:
                    cpu_percent = self.process.cpu_percent()
                    memory_mb = self.process.memory_info().rss / (1024 * 1024)
                    timestamp = time.time() - self.start_time
                    
                    self.measurements.append({
                        'timestamp': timestamp,
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_mb
                    })
                    
                    time.sleep(0.1)  # 每100ms采样一次
                except Exception as e:
                    print(f"监控错误: {e}")
                    break
        
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.start()
        return monitor_thread
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        
    def get_stats(self):
        """获取统计信息"""
        if not self.measurements:
            return {}
            
        cpu_values = [m['cpu_percent'] for m in self.measurements]
        memory_values = [m['memory_mb'] for m in self.measurements]
        
        return {
            'avg_cpu': sum(cpu_values) / len(cpu_values),
            'max_cpu': max(cpu_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'max_memory': max(memory_values),
            'sample_count': len(self.measurements)
        }

def test_config_loading_performance():
    """测试配置加载性能"""
    print("🔧 测试配置加载性能...")
    
    # 清空缓存，确保真实加载时间
    clear_config_cache()
    
    # 测试配置加载时间
    times = []
    for i in range(10):
        start_time = time.time()
        config = load_config()
        end_time = time.time()
        times.append(end_time - start_time)
        
        # 偶数次清空缓存测试真实加载，奇数次测试缓存加载
        if i % 2 == 0:
            clear_config_cache()
    
    avg_time = sum(times) / len(times)
    print(f"  ✅ 平均配置加载时间: {avg_time*1000:.2f}ms")
    print(f"  ✅ 最快加载时间: {min(times)*1000:.2f}ms")
    print(f"  ✅ 最慢加载时间: {max(times)*1000:.2f}ms")
    print(f"  ✅ 配置项数量: {len(config.get('programs', []))}")

def test_config_saving_performance():
    """测试配置保存性能"""
    print("\n💾 测试配置保存性能...")
    
    config = load_config()
    
    # 测试立即保存
    start_time = time.time()
    save_config(config, immediate=True)
    immediate_time = time.time() - start_time
    
    # 测试延迟保存
    start_time = time.time()
    save_config(config, immediate=False)
    delayed_time = time.time() - start_time
    
    print(f"  ✅ 立即保存时间: {immediate_time*1000:.2f}ms")
    print(f"  ✅ 延迟保存响应时间: {delayed_time*1000:.2f}ms")

def test_gui_responsiveness():
    """测试GUI响应性"""
    print("\n🖥️  测试GUI响应性...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # 创建主窗口
    start_time = time.time()
    window = LaunchGUI()
    window.show()
    creation_time = time.time() - start_time
    
    print(f"  ✅ 主窗口创建时间: {creation_time*1000:.2f}ms")
    
    # 测试配置刷新时间
    monitor = PerformanceMonitor()
    monitor_thread = monitor.start_monitoring(5)
    
    start_time = time.time()
    window.refresh_from_config()
    
    # 等待刷新完成
    def check_refresh_complete():
        if not hasattr(window, 'loading_overlay') or not window.loading_overlay.isVisible():
            refresh_time = time.time() - start_time
            print(f"  ✅ 配置刷新时间: {refresh_time*1000:.2f}ms")
            monitor.stop_monitoring()
            
            # 等待监控线程结束
            monitor_thread.join()
            
            # 获取性能统计
            stats = monitor.get_stats()
            if stats:
                print(f"  ✅ 刷新期间平均CPU使用率: {stats['avg_cpu']:.1f}%")
                print(f"  ✅ 刷新期间最大CPU使用率: {stats['max_cpu']:.1f}%")
                print(f"  ✅ 刷新期间平均内存使用: {stats['avg_memory']:.1f}MB")
            
            # 关闭窗口
            window.close()
            app.quit()
            return False
        return True
    
    # 创建定时器检查刷新状态
    check_timer = QTimer()
    check_timer.timeout.connect(check_refresh_complete)
    check_timer.start(100)  # 每100ms检查一次
    
    # 运行应用程序循环，直到刷新完成
    app.exec_()

def test_memory_usage():
    """测试内存使用情况"""
    print("\n💾 测试内存使用情况...")
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / (1024 * 1024)
    print(f"  ✅ 初始内存使用: {initial_memory:.1f}MB")
    
    # 多次加载配置测试内存泄漏
    for i in range(50):
        config = load_config()
        if i % 10 == 0:
            current_memory = process.memory_info().rss / (1024 * 1024)
            print(f"  📊 第{i+1}次加载后内存: {current_memory:.1f}MB")
    
    final_memory = process.memory_info().rss / (1024 * 1024)
    memory_increase = final_memory - initial_memory
    print(f"  ✅ 最终内存使用: {final_memory:.1f}MB")
    print(f"  ✅ 内存增长: {memory_increase:.1f}MB")
    
    if memory_increase < 10:
        print("  ✅ 内存使用正常，无明显泄漏")
    else:
        print("  ⚠️  内存增长较大，可能存在内存泄漏")

def run_performance_tests():
    """运行所有性能测试"""
    print("🚀 开始性能测试...")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        test_config_loading_performance()
        test_config_saving_performance()
        test_memory_usage()
        test_gui_responsiveness()
        
        total_time = time.time() - start_time
        print("\n" + "=" * 50)
        print(f"🎉 性能测试完成！总耗时: {total_time:.2f}秒")
        print("\n📋 性能优化总结:")
        print("  ✅ 配置加载：实现了缓存机制，提高加载速度")
        print("  ✅ 配置保存：实现了延迟保存，减少频繁IO")
        print("  ✅ 界面刷新：实现了异步加载，避免阻塞主线程")
        print("  ✅ 定时器优化：减少了定时器数量和频率")
        print("  ✅ 资源管理：增强了资源清理和内存管理")
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_performance_tests()