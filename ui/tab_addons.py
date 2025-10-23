# ui/tab_addons.py
import os
import importlib.util 
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QTextEdit, 
    QListWidgetItem, QAbstractItemView, QHBoxLayout
)
from PyQt5.QtCore import Qt

PLUGIN_DIR = "plugins"

class TabAddons(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.plugin_modules = {} # 存放已加载的模块
        self.initUI()
        self.discover_plugins()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("<b>插件管理器</b>"))
        layout.addWidget(QLabel(f"插件将从 './{PLUGIN_DIR}' 目录加载，勾选后可加载，取消勾选后操作以卸载。"))

        self.plugin_list_widget = QListWidget()
        self.plugin_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.plugin_list_widget)

        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("加载/卸载选中插件")
        self.load_btn.clicked.connect(self.load_selected_plugins)
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.discover_plugins)
        
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.refresh_btn)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("<b>插件日志:</b>"))
        self.plugin_log_display = QTextEdit()
        self.plugin_log_display.setReadOnly(True)
        layout.addWidget(self.plugin_log_display)

    def log(self, message):
        print(message)
        self.plugin_log_display.append(message)

    def discover_plugins(self):
        self.plugin_list_widget.clear()
        if not os.path.exists(PLUGIN_DIR):
            self.log(f"警告: 插件目录 '{PLUGIN_DIR}' 不存在。")
            os.makedirs(PLUGIN_DIR)
            self.log(f"已创建 '{PLUGIN_DIR}' 目录。")
            return
            
        self.log("正在扫描插件...")
        for filename in os.listdir(PLUGIN_DIR):
            if filename.endswith(".py") and filename != "__init__.py":
                plugin_name = filename[:-3]
                item = QListWidgetItem(plugin_name)
                item.setData(Qt.UserRole, os.path.join(PLUGIN_DIR, filename)) # 存储完整路径
                
                if plugin_name in self.plugin_modules:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                    
                self.plugin_list_widget.addItem(item)
        self.log(f"发现 {self.plugin_list_widget.count()} 个插件。")

    # def load_selected_plugins(self):
    #     for i in range(self.plugin_list_widget.count()):
    #         item = self.plugin_list_widget.item(i)
    #         if item.checkState() == Qt.Checked:
    #             plugin_name = item.text()
                
    #             if plugin_name in self.plugin_modules:
    #                 self.log(f"插件 '{plugin_name}' 已经加载。")
    #                 continue
                    
    #             plugin_path = item.data(Qt.UserRole)
    #             self.load_plugin(plugin_name, plugin_path)
    def load_selected_plugins(self):
        # 遍历列表，加载被勾选的插件，卸载未被勾选但已加载的插件。
        
        # 遍历所有项目
        for i in range(self.plugin_list_widget.count()):
            item = self.plugin_list_widget.item(i)
            plugin_name = item.text()
            plugin_path = item.data(Qt.UserRole)
            
            is_loaded = plugin_name in self.plugin_modules
            is_checked = item.checkState() == Qt.Checked
            
            if is_checked:
                # 勾选且未加载 执行加载
                if not is_loaded:
                    self.load_plugin(plugin_name, plugin_path)
            else:
                # 未勾选且已加载 执行卸载
                if is_loaded:
                    self.unload_plugin(plugin_name)
        self.log("操作完成。")

    def load_plugin(self, plugin_name, plugin_path):
        self.log(f"--- 正在加载插件: {plugin_name} ---")
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None:
                raise ImportError(f"无法为 {plugin_path} 创建 spec")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "register"):
                module.register(self.main_window)
                self.plugin_modules[plugin_name] = module
                self.log(f"插件 '{plugin_name}' 加载并注册成功。")
            else:
                self.log(f"错误: 插件 '{plugin_name}' 没有发现register项目。")
                
        except Exception as e:
            self.log(f"!!! 加载插件 '{plugin_name}' 失败: {e}")
            import traceback
            self.log(traceback.format_exc())
            
    def unload_plugin(self, plugin_name):
        # 卸载并从 self.plugin_modules 移除插件
        if plugin_name in self.plugin_modules:
            self.log(f"--- 正在卸载插件: {plugin_name} ---")
            module = self.plugin_modules[plugin_name]
            
            try:
                # 检查是否存在 unregister 函数并调用
                if hasattr(module, "unregister"):
                    module.unregister(self.main_window)
                    self.log(f"插件 '{plugin_name}' unregister执行成功。")
                
                # 移除模块引用
                del self.plugin_modules[plugin_name]
                self.log(f"插件 '{plugin_name}' 卸载成功。")

            except Exception as e:
                self.log(f"!!! 卸载插件 '{plugin_name}' 失败: {e}")
                import traceback
                self.log(traceback.format_exc())