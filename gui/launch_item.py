#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QApplication, QFrame, QGraphicsDropShadowEffect, QMenu, QSizePolicy)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QFont, QCursor, QColor
from utils.app_launcher import open_app
from gui.flow_layout import FlowLayout
from utils.logger import get_logger
from utils.platform_settings import (is_windows, is_mac, is_linux, 
                                    get_platform_style, get_platform_setting)

# 获取日志记录器
logger = get_logger()

class ParamLabel(QLabel):
    """可点击的参数标签"""
    def __init__(self, param, parent=None):
        # 处理空字符串参数
        if not param:
            param = "<空>"
        super().__init__(param, parent)
        self.param = param
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # 使用平台特定样式
        self.setStyleSheet(get_platform_style('param_label'))
        
        # 设置适合当前平台的字体大小
        font = self.font()
        font_size = get_platform_setting('font_sizes.param_label')
        font.setPointSize(font_size)
        self.setFont(font)

class LaunchItem(QFrame):
    """启动项组件"""
    def __init__(self, name, app, params=None, source_category=None):
        super().__init__()
        self.name = name
        self.app = app
        self.params = params or []
        self.category_tab = None
        self.source_category = source_category  # 添加所属分类属性
        self.is_selected = False  # 添加选中状态
        
        # 记录创建启动项的日志
        logger.debug(f"创建启动项: 名称={name}, 应用={app}, 参数={params}")
        
        # 设置为卡片样式并添加阴影效果
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setFocusPolicy(Qt.StrongFocus)  # 确保可以接收焦点和键盘事件
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))  # 半透明黑色
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 根据平台设置布局边距和间距
        margins = get_platform_setting('layouts.launch_item_margins')
        spacing = get_platform_setting('layouts.launch_item_spacing')
        main_layout.setContentsMargins(*margins)
        main_layout.setSpacing(spacing)
        
        # 确保整个内容区域不会超出父控件范围
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        # 创建标题栏
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            background-color: #f0f0f0;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 15, 10, 15)  # 增加标题栏内边距
        
        # 创建标题标签，根据平台处理长标题
        title_name = name
        # 如果名称过长，根据平台设置截断显示
        max_title_length = get_platform_setting('max_title_length')
        if max_title_length and len(title_name) > max_title_length:
            title_name = title_name[:max_title_length-2] + "..."
            
        title_label = QLabel(title_name)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(get_platform_setting('font_sizes.title'))
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: black; background-color: transparent;")
        
        # 添加到标题栏布局
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        
        # 添加标题栏到主布局
        main_layout.addWidget(title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 根据平台设置内容区域边距和间距
        content_margins = get_platform_setting('layouts.content_margins')
        content_spacing = get_platform_setting('layouts.content_spacing')
        content_layout.setContentsMargins(*content_margins)
        content_layout.setSpacing(content_spacing)
        
        # 应用信息
        app_name = os.path.basename(app) if os.path.isabs(app) else app
        app_label = QLabel(f"应用: {app_name}")
        app_label.setStyleSheet(get_platform_style('app_label'))
        app_font = app_label.font()
        app_font.setPointSize(get_platform_setting('font_sizes.app_label'))
        app_label.setFont(app_font)
        content_layout.addWidget(app_label)
        
        # 如果有所属分类且不是在原分类中显示，则显示分类信息
        if source_category:
            category_label = QLabel(f"分类: {source_category}")
            category_label.setStyleSheet(get_platform_style('category_label'))
            category_font = category_label.font()
            category_font.setPointSize(get_platform_setting('font_sizes.category_label'))
            category_label.setFont(category_font)
            content_layout.addWidget(category_label)
        
        # 参数信息
        if params:
            params_layout = QVBoxLayout()
            params_layout.setSpacing(get_platform_setting('layouts.params_spacing'))
            params_layout.setContentsMargins(0, get_platform_setting('layouts.params_top_margin'), 0, 0)
            
            params_header = QHBoxLayout()
            params_label = QLabel("参数:")
            params_label.setStyleSheet(get_platform_style('params_label'))
            params_font = params_label.font()
            params_font.setPointSize(get_platform_setting('font_sizes.params_label'))
            params_label.setFont(params_font)
            params_header.addWidget(params_label)
            params_header.addStretch()
            params_layout.addLayout(params_header)
            
            # 创建流式布局容器
            flow_layout = FlowLayout()
            flow_layout.setSpacing(get_platform_setting('layouts.param_labels_spacing'))
            
            # 添加每个参数作为可点击的标签
            for param in params:
                param_label = ParamLabel(str(param))
                param_label.mousePressEvent = lambda event, p=param: self.launch_with_param(p)
                flow_layout.addWidget(param_label)
            
            # 将流式布局添加到参数布局
            params_layout.addLayout(flow_layout)
            content_layout.addLayout(params_layout)
        
        # 添加内容区域到主布局
        main_layout.addWidget(content_widget)
        main_layout.setStretch(1, 1)  # 让内容区域填充剩余空间
        
        # 设置样式
        self.setStyleSheet(get_platform_style('launch_item'))
        
        # 根据内容自动调整高度
        base_height = get_platform_setting('base_heights.launch_item')
        
        if source_category:
            base_height += get_platform_setting('base_heights.category_add')
        
        if params:
            # 参数数量和复杂度会影响高度，根据平台计算参数部分高度
            param_count_threshold = get_platform_setting('param_count_threshold')
            param_height_base = get_platform_setting('base_heights.param_base')
            param_height_per_row = get_platform_setting('base_heights.param_per_row')
            
            param_height = param_height_base
            if len(params) > param_count_threshold:
                # 计算额外行数，假设每行约3个参数
                extra_rows = (len(params) - param_count_threshold) // 3
                param_height += extra_rows * param_height_per_row
            
            base_height += param_height
        
        self.setMinimumHeight(base_height)
        # 不设置最大高度，让内容自适应
        self.setMaximumHeight(16777215)  # Qt默认的最大值
        
        # 让布局自动调整内容高度
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置提示
        self.setToolTip("双击启动应用")
        
        # 设置光标
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def set_category_tab(self, category_tab):
        """设置所属分类标签页"""
        self.category_tab = category_tab
    
    def update_display(self):
        """更新显示内容"""
        # 更新标题
        if self.layout().count() > 0:
            title_bar = self.layout().itemAt(0).widget()
            if title_bar and title_bar.layout() and title_bar.layout().count() > 0:
                title_label = title_bar.layout().itemAt(0).widget()
                if title_label and isinstance(title_label, QLabel):
                    # 如果名称过长，根据平台设置截断显示
                    title_name = self.name
                    max_title_length = get_platform_setting('max_title_length')
                    if max_title_length and len(title_name) > max_title_length:
                        title_name = title_name[:max_title_length-2] + "..."
                    title_label.setText(title_name)
        
        # 更新内容区域
        if self.layout().count() > 1:
            content_widget = self.layout().itemAt(1).widget()
            if content_widget and content_widget.layout():
                content_layout = content_widget.layout()
                
                # 更新应用信息
                if content_layout.count() > 0:
                    app_label = content_layout.itemAt(0).widget()
                    if app_label and isinstance(app_label, QLabel):
                        app_name = os.path.basename(self.app) if os.path.isabs(self.app) else self.app
                        app_label.setText(f"应用: {app_name}")
                        app_label.setStyleSheet(get_platform_style('app_label'))
                        app_font = app_label.font()
                        app_font.setPointSize(get_platform_setting('font_sizes.app_label'))
                        app_label.setFont(app_font)
                
                # 更新参数信息 - 需要移除旧的参数布局并创建新的
                # 首先找到参数布局的索引
                params_layout_index = -1
                for i in range(content_layout.count()):
                    item = content_layout.itemAt(i)
                    if item.layout():
                        # 这可能是参数布局
                        for j in range(item.layout().count()):
                            subitem = item.layout().itemAt(j)
                            if subitem.widget() and isinstance(subitem.widget(), QLabel) and subitem.widget().text() == "参数:":
                                params_layout_index = i
                                break
                
                # 如果找到了参数布局，移除它
                if params_layout_index >= 0:
                    params_layout = content_layout.itemAt(params_layout_index).layout()
                    self._clear_layout(params_layout)
                    # 移除空的布局
                    widget = content_layout.itemAt(params_layout_index).widget()
                    if widget:
                        content_layout.removeWidget(widget)
                        widget.deleteLater()
                
                # 如果有参数，添加新的参数布局
                if self.params:
                    params_layout = QVBoxLayout()
                    params_layout.setSpacing(get_platform_setting('layouts.params_spacing'))
                    params_layout.setContentsMargins(0, get_platform_setting('layouts.params_top_margin'), 0, 0)
                    
                    params_header = QHBoxLayout()
                    params_label = QLabel("参数:")
                    params_label.setStyleSheet(get_platform_style('params_label'))
                    params_font = params_label.font()
                    params_font.setPointSize(get_platform_setting('font_sizes.params_label'))
                    params_label.setFont(params_font)
                    params_header.addWidget(params_label)
                    params_header.addStretch()
                    params_layout.addLayout(params_header)
                    
                    # 创建流式布局容器
                    flow_layout = FlowLayout()
                    flow_layout.setSpacing(get_platform_setting('layouts.param_labels_spacing'))
                    
                    # 添加每个参数作为可点击的标签
                    for param in self.params:
                        param_label = ParamLabel(str(param))
                        param_label.mousePressEvent = lambda event, p=param: self.launch_with_param(p)
                        flow_layout.addWidget(param_label)
                    
                    # 将流式布局添加到参数布局
                    params_layout.addLayout(flow_layout)
                    
                    # 添加参数布局到内容布局
                    content_layout.addLayout(params_layout)
    
    def _clear_layout(self, layout):
        """清空布局中的所有控件"""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget:
                widget.deleteLater()
            else:
                # 如果是子布局，递归清空
                self._clear_layout(item.layout())
    
    def launch(self):
        """启动应用"""
        try:
            open_app(self.app, self.params)
            logger.info(f"启动应用: {self.app}")
        except Exception as e:
            logger.error(f"启动应用失败: {self.app}, 错误: {str(e)}")
    
    def launch_with_param(self, param):
        """使用单个参数启动应用"""
        try:
            from utils.app_launcher import open_app
            open_app(self.app, [param])
            logger.info(f"启动应用(单参数): {self.app} {param}")
        except Exception as e:
            logger.error(f"启动应用失败(单参数): {self.app} {param}, 错误: {str(e)}")
    
    def mouseDoubleClickEvent(self, event):
        """双击启动应用"""
        if event.button() == Qt.LeftButton:
            self.launch()
            event.accept()
    
    # 鼠标事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            
            # 处理选中状态
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                # Ctrl+点击，切换选中状态
                self.toggle_selected()
            elif QApplication.keyboardModifiers() & Qt.ShiftModifier:
                # Shift+点击，选择范围
                if self.category_tab:
                    # 找到最后一个选中的项目
                    last_selected = None
                    if self.category_tab.selected_items:
                        last_selected = self.category_tab.selected_items[-1]
                    
                    if last_selected:
                        # 找到当前项目和最后选中项目的索引
                        current_index = -1
                        last_index = -1
                        items = []
                        
                        # 收集所有项目并找到索引
                        for i in range(self.category_tab.content_layout.count()):
                            widget = self.category_tab.content_layout.itemAt(i).widget()
                            if isinstance(widget, LaunchItem):
                                items.append(widget)
                                if widget == self:
                                    current_index = len(items) - 1
                                if widget == last_selected:
                                    last_index = len(items) - 1
                        
                        if current_index != -1 and last_index != -1:
                            # 确定选择范围
                            start_index = min(current_index, last_index)
                            end_index = max(current_index, last_index)
                            
                            # 选择范围内的所有项目
                            for i in range(start_index, end_index + 1):
                                items[i].set_selected(True)
                    else:
                        # 如果没有已选中的项目，只选中当前项目
                        self.set_selected(True)
            else:
                # 普通点击，清除其他选中项，选中当前项
                if self.category_tab:
                    for item in self.category_tab.selected_items:
                        if item != self:
                            item.set_selected(False)
                    self.category_tab.selected_items = []
                self.set_selected(True)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        # 检查是否达到拖动阈值
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # 创建拖放对象
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 设置MIME类型和数据
        mime_data.setData("application/x-launch-item", b"launch-item")
        drag.setMimeData(mime_data)
        
        # 设置拖动时的图像
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # 执行拖放操作
        result = drag.exec_(Qt.MoveAction)
    
    def toggle_selected(self):
        """切换选中状态"""
        self.set_selected(not self.is_selected)
    
    def set_selected(self, selected):
        """设置选中状态"""
        if self.is_selected == selected:
            return  # 状态没有变化，不需要处理
        
        self.is_selected = selected
        
        # 设置样式
        self._update_selection_style()
        
        # 更新选中列表
        if self.category_tab:
            if selected and self not in self.category_tab.selected_items:
                self.category_tab.selected_items.append(self)
            elif not selected and self in self.category_tab.selected_items:
                self.category_tab.selected_items.remove(self)
    
    def _update_selection_style(self):
        """更新选中状态的样式"""
        # 设置主框架样式
        if self.is_selected:
            self.setStyleSheet("""
                LaunchItem {
                    background-color: #e6f7ff;
                    border: 2px solid #1890ff;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("")
        
        # 更新标题栏样式
        if self.layout().count() > 0:
            title_bar = self.layout().itemAt(0).widget()
            if title_bar:
                bg_color = "#bae7ff" if self.is_selected else "#f0f0f0"
                title_bar.setStyleSheet(f"""
                    background-color: {bg_color};
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                """)
        
        # 更新参数标签样式
        self._update_param_labels_style()
    
    def _update_param_labels_style(self):
        """更新参数标签样式"""
        # 查找参数布局
        if self.layout().count() > 1:
            content_widget = self.layout().itemAt(1).widget()
            if content_widget and content_widget.layout():
                content_layout = content_widget.layout()
                for i in range(content_layout.count()):
                    item = content_layout.itemAt(i)
                    if item.layout():
                        # 查找参数布局
                        for j in range(item.layout().count()):
                            subitem = item.layout().itemAt(j)
                            if subitem.layout():
                                # 查找流式布局
                                flow_layout = subitem.layout()
                                for k in range(flow_layout.count()):
                                    param_widget = flow_layout.itemAt(k).widget()
                                    if isinstance(param_widget, ParamLabel):
                                        param_widget.setStyleSheet(get_platform_style('param_label_selected' if self.is_selected else 'param_label'))
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        # 如果没有选中，先选中当前项
        if not self.is_selected:
            # 清除其他选中项
            if self.category_tab:
                for item in self.category_tab.selected_items:
                    item.set_selected(False)
                self.category_tab.selected_items = []
            
            # 选中当前项
            self.set_selected(True)
        
        # 调用标签页的右键菜单显示方法
        if self.category_tab:
            self.category_tab.show_item_context_menu(event.pos(), self)
        
        menu = QMenu(self)
        menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        """处理键盘按键事件"""
        # 回车键直接启动应用
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.launch()
            return
        
        # 上下键事件让父窗口处理，以便进行导航
        if event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
            # 不调用父类的keyPressEvent，让事件继续冒泡到应用程序范围
            event.ignore()
            return
        
        # 其他键盘事件按默认方式处理
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        """获得焦点时的处理"""
        # 当获得焦点时，确保项目被选中
        if not self.is_selected and self.category_tab and hasattr(self.category_tab, "main_window"):
            main_window = self.category_tab.main_window
            if main_window:
                self._update_selection_in_visible_items(main_window)
        
        super().focusInEvent(event)
    
    def _update_selection_in_visible_items(self, main_window):
        """更新可见项目中的选中状态"""
        # 获取所有可见项目
        visible_items = []
        for i in range(self.category_tab.content_layout.count()):
            widget = self.category_tab.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, LaunchItem) and widget.isVisible():
                visible_items.append(widget)
        
        try:
            index = visible_items.index(self)
            # 更新当前选中索引
            main_window.current_selected_index = index
            # 清除其他选中
            for item in visible_items:
                if item != self:
                    item.set_selected(False)
            # 选中当前项目
            self.set_selected(True)
        except ValueError:
            pass  # 项目不在可见列表中