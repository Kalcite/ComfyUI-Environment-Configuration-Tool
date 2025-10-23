# ui/tab_project_path.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, 
    QLabel, QGroupBox, QMessageBox
)

class TabProjectPath(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        group = QGroupBox("选择 ComfyUI 根目录")
        group_layout = QVBoxLayout()
        
        h_layout = QHBoxLayout()
        self.project_dir_lineedit = QLineEdit()
        self.project_dir_lineedit.setReadOnly(True)
        h_layout.addWidget(QLabel("ComfyUI 目录:"))
        h_layout.addWidget(self.project_dir_lineedit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.select_project_dir)
        h_layout.addWidget(browse_btn)
        
        group_layout.addLayout(h_layout)
        
        self.project_status_label = QLabel("状态: 未选择")
        self.project_status_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.project_status_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def select_project_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择 ComfyUI 根目录")
        if directory:
            if self.validate_project_dir(directory):
                self.main_window.project_dir = directory # 更新主窗口的共享变量
                self.project_dir_lineedit.setText(self.main_window.project_dir)
                self.project_status_label.setText("状态: [锁定] 找到目标文件。")
                self.project_status_label.setStyleSheet("color: green;")
                self.main_window.save_config() # 调用主窗口的保存
            else:
                QMessageBox.warning(self, "路径无效", "所选目录中未找到 'main.py' 和/或 'requirements.txt'。")
                self.project_status_label.setText("状态: 路径无效")
                self.project_status_label.setStyleSheet("color: red;")

    def validate_project_dir(self, directory):
        main_py = os.path.join(directory, 'main.py')
        req_txt = os.path.join(directory, 'requirements.txt')
        return os.path.exists(main_py) and os.path.exists(req_txt)

    def update_ui_from_config(self, project_dir):
        """由 main_app 调用，用于在启动时加载配置"""
        if project_dir and self.validate_project_dir(project_dir):
            self.project_dir_lineedit.setText(project_dir)
            self.project_status_label.setText("状态: [已加载] 路径有效。")
            self.project_status_label.setStyleSheet("color: green;")