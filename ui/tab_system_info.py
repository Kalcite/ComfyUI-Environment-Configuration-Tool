# ui/tab_system_info.py
import wmi
import subprocess
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt

class TabSystemInfo(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        self.hel_text_edit = QTextEdit(self)
        self.hel_text_edit.setReadOnly(True)
        self.hel_text_edit.setMaximumHeight(200)
        hel_text = (
            "作者：https://github.com/Kalcite   BiliBili：1999Pt\n"
            "本工具目前仅限支持ROCm6.4版本及以上的GPU使用，例如7800XT或9070XT\n"
            "现已支持nvidia显卡部署环境，从仓库下载最新nvidia支持插件即可\n"
            "参考文档:\n"
            "https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html\n"
            "https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/\n"
            "https://www.amd.com/en/resources/support-articles/release-notes/RN-AMDGPU-WINDOWS-PYTORCH-PREVIEW.html\n"
        )
        self.hel_text_edit.setText(hel_text)
        layout.addWidget(self.hel_text_edit)
        
        layout.addWidget(QLabel("<b>GPU信息:</b>"))
        self.gpu_info_text = QTextEdit()
        self.gpu_info_text.setReadOnly(True)
        self.gpu_info_text.setFixedHeight(100)
        layout.addWidget(self.gpu_info_text)
        
        layout.addWidget(QLabel("<b>系统 Python 解释器:</b>"))
        self.python_list_widget = QListWidget()
        layout.addWidget(self.python_list_widget)
        
        refresh_btn = QPushButton("刷新检测信息")
        refresh_btn.clicked.connect(self.refresh_tab1_info)
        layout.addWidget(refresh_btn)

    def refresh_tab1_info(self):
        # 1. 检测显卡
        self.gpu_info_text.clear()
        try:
            w = wmi.WMI()
            gpus = w.Win32_VideoController()
            self.gpu_info_text.append("检测到以下显卡:")
            found_amd = False
            for gpu in gpus:
                self.gpu_info_text.append(f"- {gpu.Name}")
                if "amd" in gpu.Name.lower() or "radeon" in gpu.Name.lower():
                    found_amd = True
            if not found_amd:
                self.gpu_info_text.append("\n<b>[警告] 未检测到 AMD 显卡。</b>")
        except Exception as e:
            self.gpu_info_text.append(f"检测显卡失败: {e}\n尝试使用 'wmic'...\n")
            try:
                result = subprocess.check_output(['wmic', 'path', 'Win32_VideoController', 'get', 'Name']).decode('utf-8')
                self.gpu_info_text.append(result)
            except Exception as e2:
                self.gpu_info_text.append(f"'wmic' 失败: {e2}")

        # 2. 检测 Python
        self.python_list_widget.clear()
        self.main_window.python_interpreters.clear() # 更新主窗口的共享变量
        try:
            paths = set()
            for cmd in ['python', 'python3', 'py']:
                try:
                    result = subprocess.check_output(['where', cmd]).decode('utf-8')
                    paths.update(result.strip().split('\r\n'))
                except subprocess.CalledProcessError:
                    pass 

            for path in paths:
                if path and "WindowsApps" not in path and os.path.exists(path):
                    try:
                        version_output = subprocess.check_output([path, '--version'], stderr=subprocess.STDOUT).decode('utf-8').strip()
                        version = version_output.split(" ")[1]
                        self.main_window.python_interpreters[path] = version # 存入共享变量
                        item = QListWidgetItem(f"版本: {version}  |  路径: {path}")
                        if "3.12" in version:
                            item.setBackground(Qt.yellow) 
                        self.python_list_widget.addItem(item)
                    except Exception:
                        pass 
            
            # --- 跨Tab通信 ---
            # 刷新Tab3的Python 列表
            if hasattr(self.main_window, 'tab3'):
                self.main_window.tab3.update_tab3_python_selector()

        except Exception as e:

            self.python_list_widget.addItem(f"查找 Python 失败: {e}")
