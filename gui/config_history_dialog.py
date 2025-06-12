#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
                           QListWidgetItem, QSplitter, QLabel, QPlainTextEdit, QMessageBox,
                           QInputDialog, QWidget, QTabWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QTextCharFormat, QBrush, QColor

from utils.config_history import ConfigHistoryManager
from utils.logger import get_logger
import json

class ConfigHistoryDialog(QDialog):
    """配置历史记录查看和对比对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.history_manager = ConfigHistoryManager()
        
        self.setWindowTitle("历史变更记录")
        self.resize(900, 600)
        
        # 创建布局
        self.create_ui()
        
        # 加载历史记录列表
        self.load_history_list()
    
    def create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧历史记录列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        history_label = QLabel("历史记录")
        left_layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.setMinimumWidth(300)
        self.history_list.currentItemChanged.connect(self.on_history_selected)
        left_layout.addWidget(self.history_list)
        
        # 历史记录按钮
        history_buttons_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_history_list)
        history_buttons_layout.addWidget(self.refresh_btn)
        
        self.restore_btn = QPushButton("恢复")
        self.restore_btn.clicked.connect(self.restore_history)
        self.restore_btn.setEnabled(False)
        history_buttons_layout.addWidget(self.restore_btn)
        
        left_layout.addLayout(history_buttons_layout)
        
        # 右侧历史记录内容和对比
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        self.content_tab = QWidget()
        self.diff_tab = QWidget()
        
        # 内容标签页
        content_layout = QVBoxLayout(self.content_tab)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.content_text = QPlainTextEdit()
        self.content_text.setReadOnly(True)
        content_layout.addWidget(self.content_text)
        
        # 差异对比标签页
        diff_layout = QVBoxLayout(self.diff_tab)
        diff_layout.setContentsMargins(5, 5, 5, 5)
        
        diff_controls = QHBoxLayout()
        diff_layout.addLayout(diff_controls)
        
        self.compare_label = QLabel("选择要对比的历史记录:")
        diff_controls.addWidget(self.compare_label)
        
        self.compare_btn = QPushButton("对比")
        self.compare_btn.clicked.connect(self.compare_with_current)
        self.compare_btn.setEnabled(False)
        diff_controls.addWidget(self.compare_btn)
        
        self.compare_with_another_btn = QPushButton("对比其他版本")
        self.compare_with_another_btn.clicked.connect(self.compare_with_another)
        self.compare_with_another_btn.setEnabled(False)
        diff_controls.addWidget(self.compare_with_another_btn)
        
        diff_controls.addStretch()
        
        self.diff_text = QPlainTextEdit()
        self.diff_text.setReadOnly(True)
        # 设置等宽字体
        self.diff_text.setStyleSheet("font-family: Consolas, Menlo, Monaco, 'Courier New', monospace; font-size: 14px;")
        diff_layout.addWidget(self.diff_text)
        
        # 添加标签页
        self.tab_widget.addTab(self.content_tab, "内容")
        self.tab_widget.addTab(self.diff_tab, "差异对比")
        
        right_layout.addWidget(self.tab_widget)
        
        # 将左右两个小部件添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # 设置初始分割比例
        splitter.setSizes([300, 600])
        
        # 将分割器添加到主布局
        layout.addWidget(splitter)
        
        # 底部按钮
        buttons_layout = QHBoxLayout()
        
        self.save_current_btn = QPushButton("保存当前配置为新历史记录")
        self.save_current_btn.clicked.connect(self.save_current_history)
        buttons_layout.addWidget(self.save_current_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_history_list(self):
        """加载历史记录列表"""
        try:
            # 获取历史记录
            history_list = self.history_manager.get_history_list()
            
            # 清空列表
            self.history_list.clear()
            
            # 添加历史记录项目
            for history in history_list:
                item = QListWidgetItem(f"{history['date']}")
                if history['description']:
                    item.setToolTip(history['description'])
                    # 设置第二行显示描述，限制长度
                    desc = history['description']
                    if len(desc) > 30:
                        desc = desc[:27] + "..."
                    item.setText(f"{history['date']}\n{desc}")
                item.setData(Qt.UserRole, history)
                self.history_list.addItem(item)
            
            # 禁用恢复和对比按钮
            self.restore_btn.setEnabled(False)
            self.compare_btn.setEnabled(False)
            self.compare_with_another_btn.setEnabled(False)
            
            # 清空内容和差异文本
            self.content_text.clear()
            self.diff_text.clear()
            
        except Exception as e:
            self.logger.error(f"加载历史记录列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载历史记录列表失败: {e}")
    
    def on_history_selected(self, current, previous):
        """处理历史记录选择变更"""
        if current is None:
            self.restore_btn.setEnabled(False)
            self.compare_btn.setEnabled(False)
            self.compare_with_another_btn.setEnabled(False)
            self.content_text.clear()
            return
        
        try:
            # 获取选中的历史记录
            history_data = current.data(Qt.UserRole)
            
            # 启用按钮
            self.restore_btn.setEnabled(True)
            self.compare_btn.setEnabled(True)
            self.compare_with_another_btn.setEnabled(True)
            
            # 获取历史记录内容
            history_content, error = self.history_manager.get_history_content(history_data['filename'])
            
            if error or history_content is None:
                self.content_text.clear()
                QMessageBox.warning(self, "警告", f"无法加载历史记录内容: {error}")
                return
            
            # 显示内容（格式化为美观的JSON）
            config_data = history_content.get("config", {})
            formatted_json = json.dumps(config_data, ensure_ascii=False, indent=2)
            self.content_text.setPlainText(formatted_json)
            
            # 如果在差异对比标签页，则自动执行对比
            if self.tab_widget.currentIndex() == 1:
                self.compare_with_current()
        
        except Exception as e:
            self.logger.error(f"加载历史记录内容失败: {e}")
            QMessageBox.critical(self, "错误", f"加载历史记录内容失败: {e}")
    
    def compare_with_current(self):
        """将选中的历史记录与当前配置进行对比"""
        try:
            current_item = self.history_list.currentItem()
            if current_item is None:
                return
            
            # 获取选中的历史记录
            history_data = current_item.data(Qt.UserRole)
            
            # 获取历史记录内容
            history_content, error = self.history_manager.get_history_content(history_data['filename'])
            
            if error or history_content is None:
                QMessageBox.warning(self, "警告", f"无法加载历史记录内容: {error}")
                return
            
            # 获取历史配置
            old_config = history_content.get("config", {})
            
            # 获取当前配置
            from utils.config_manager import load_config
            current_config = load_config()
            
            # 对比配置
            diff_lines = self.history_manager.compare_configs(old_config, current_config)
            
            # 设置差异文本
            self.diff_text.clear()
            self.diff_text.setPlainText("\n".join(diff_lines))
            
            # 高亮差异
            self.highlight_diff()
            
            # 切换到差异标签页
            self.tab_widget.setCurrentIndex(1)
        
        except Exception as e:
            self.logger.error(f"对比配置失败: {e}")
            QMessageBox.critical(self, "错误", f"对比配置失败: {e}")
    
    def compare_with_another(self):
        """将选中的历史记录与另一个历史记录进行对比"""
        try:
            current_item = self.history_list.currentItem()
            if current_item is None:
                return
            
            # 获取选中的历史记录
            selected_history = current_item.data(Qt.UserRole)
            
            # 获取所有历史记录
            histories = self.history_manager.get_history_list()
            
            # 移除当前选中的历史记录
            histories = [h for h in histories if h['filename'] != selected_history['filename']]
            
            # 如果没有其他历史记录，提示用户
            if not histories:
                QMessageBox.information(self, "提示", "没有其他历史记录可供对比")
                return
            
            # 创建选择对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("选择对比的历史记录")
            dialog.resize(500, 300)
            
            layout = QVBoxLayout(dialog)
            
            label = QLabel("选择要对比的历史记录:")
            layout.addWidget(label)
            
            list_widget = QListWidget()
            layout.addWidget(list_widget)
            
            # 添加历史记录项目
            for history in histories:
                item = QListWidgetItem(f"{history['date']}")
                if history['description']:
                    item.setToolTip(history['description'])
                    # 设置第二行显示描述，限制长度
                    desc = history['description']
                    if len(desc) > 30:
                        desc = desc[:27] + "..."
                    item.setText(f"{history['date']}\n{desc}")
                item.setData(Qt.UserRole, history)
                list_widget.addItem(item)
            
            # 添加按钮
            buttons_layout = QHBoxLayout()
            
            ok_button = QPushButton("确定")
            ok_button.clicked.connect(dialog.accept)
            buttons_layout.addWidget(ok_button)
            
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(dialog.reject)
            buttons_layout.addWidget(cancel_button)
            
            layout.addLayout(buttons_layout)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                # 获取选择的历史记录
                selected_item = list_widget.currentItem()
                if selected_item:
                    compare_history = selected_item.data(Qt.UserRole)
                    
                    # 获取两个历史记录的内容
                    history1_content, error1 = self.history_manager.get_history_content(selected_history['filename'])
                    history2_content, error2 = self.history_manager.get_history_content(compare_history['filename'])
                    
                    if error1 or history1_content is None:
                        QMessageBox.warning(self, "警告", f"无法加载历史记录内容: {error1}")
                        return
                    
                    if error2 or history2_content is None:
                        QMessageBox.warning(self, "警告", f"无法加载对比历史记录内容: {error2}")
                        return
                    
                    # 获取配置
                    config1 = history1_content.get("config", {})
                    config2 = history2_content.get("config", {})
                    
                    # 对比配置
                    diff_lines = self.history_manager.compare_configs(config1, config2)
                    
                    # 设置差异文本
                    self.diff_text.clear()
                    
                    # 添加标题
                    title = f"对比: {selected_history['date']} VS {compare_history['date']}\n"
                    title += "=" * 80 + "\n\n"
                    self.diff_text.appendPlainText(title)
                    
                    # 添加差异内容
                    self.diff_text.appendPlainText("\n".join(diff_lines))
                    
                    # 高亮差异
                    self.highlight_diff()
                    
                    # 切换到差异标签页
                    self.tab_widget.setCurrentIndex(1)
        
        except Exception as e:
            self.logger.error(f"对比历史记录失败: {e}")
            QMessageBox.critical(self, "错误", f"对比历史记录失败: {e}")
    
    def highlight_diff(self):
        """高亮显示差异"""
        document = self.diff_text.document()
        
        # 为文档中的所有文本设置默认格式
        cursor = self.diff_text.textCursor()
        cursor.select(cursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()
        
        # 逐行处理文本
        block = document.begin()
        while block.isValid():
            line = block.text()
            
            # 创建格式对象
            format = QTextCharFormat()
            
            # 根据行的前缀设置颜色
            if line.startswith('+'):
                # 添加行 - 绿色
                format.setForeground(QBrush(QColor("#008800")))
                format.setBackground(QBrush(QColor("#EAFFEA")))
            elif line.startswith('-'):
                # 删除行 - 红色
                format.setForeground(QBrush(QColor("#CC0000")))
                format.setBackground(QBrush(QColor("#FFECEC")))
            elif line.startswith('?'):
                # 提示行 - 蓝色
                format.setForeground(QBrush(QColor("#0000CC")))
            
            # 应用格式
            if format.foreground().color() != QColor():
                cursor.setPosition(block.position())
                cursor.setPosition(block.position() + block.length() - 1, cursor.KeepAnchor)
                cursor.setCharFormat(format)
            
            block = block.next()
    
    def restore_history(self):
        """恢复到选中的历史记录"""
        try:
            current_item = self.history_list.currentItem()
            if current_item is None:
                return
            
            # 获取选中的历史记录
            history_data = current_item.data(Qt.UserRole)
            
            # 确认恢复
            confirm = QMessageBox.question(
                self, "确认恢复", 
                f"确定要恢复到 {history_data['date']} 的配置吗？\n当前配置将会丢失。",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # 恢复配置
                success, message = self.history_manager.restore_config(history_data['filename'])
                
                if success:
                    QMessageBox.information(self, "恢复成功", message)
                    # 刷新列表
                    self.load_history_list()
                    # 发出配置变更信号
                    self.parent().refresh_from_config()
                else:
                    QMessageBox.warning(self, "恢复失败", message)
        
        except Exception as e:
            self.logger.error(f"恢复历史记录失败: {e}")
            QMessageBox.critical(self, "错误", f"恢复历史记录失败: {e}")
    
    def save_current_history(self):
        """保存当前配置作为新的历史记录"""
        try:
            # 获取描述
            description, ok = QInputDialog.getText(
                self, "保存历史记录", "请输入历史记录描述:",
                text=""
            )
            
            if ok:
                # 保存历史记录
                success, result = self.history_manager.save_history(description=description)
                
                if success:
                    QMessageBox.information(self, "保存成功", f"历史记录已保存")
                    # 刷新列表
                    self.load_history_list()
                else:
                    QMessageBox.warning(self, "保存失败", result)
        
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")
            QMessageBox.critical(self, "错误", f"保存历史记录失败: {e}") 