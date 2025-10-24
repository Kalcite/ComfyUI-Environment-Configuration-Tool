# ui/tab_launch_options.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFormLayout
)

class TabLaunchOptions(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        self.help_text_edit = QTextEdit(self)
        self.help_text_edit.setReadOnly(True)
        self.help_text_edit.setMaximumHeight(300)
        
        help_text = (
            "【ComfyUI 启动参数说明】\n\n"
            "  --listen <地址>: 设置监听地址，默认 127.0.0.1 (本地访问)。\n"
            "  --port <端口>: 设置监听端口，默认 8188。\n"
            "--cpu：所有计算都在 CPU 上完成（速度较慢）。\n"
        )
        self.help_text_edit.setText(help_text)
        layout.addWidget(self.help_text_edit)
        
        form_layout = QFormLayout()
        
        self.listen_addr_lineedit = QLineEdit("127.0.0.1")
        self.port_lineedit = QLineEdit("8188")
        self.other_args_lineedit = QLineEdit()
        self.other_args_lineedit.setPlaceholderText("例如: --preview-method auto --disable-smart-memory")
        
        form_layout.addRow(QLabel("监听地址 (--listen):"), self.listen_addr_lineedit)
        form_layout.addRow(QLabel("监听端口 (--port):"), self.port_lineedit)
        form_layout.addRow(QLabel("其他启动参数:"), self.other_args_lineedit)
        
        layout.addWidget(QLabel("<b>自定义 ComfyUI 启动参数:</b>"))
        layout.addLayout(form_layout)
        
        save_btn = QPushButton("保存启动设置")
        save_btn.clicked.connect(self.main_window.save_config) # 直接调用主窗口的保存
        layout.addWidget(save_btn)
        
        layout.addStretch()

    # --- Getter 方法供 Tab 6 和 main_app 调用 ---
    def get_listen_addr(self):
        return self.listen_addr_lineedit.text()

    def get_port(self):
        return self.port_lineedit.text()

    def get_other_args(self):
        return self.other_args_lineedit.text()

    def update_ui_from_config(self, launch_args_config):
        """由 main_app 调用，用于在启动时加载配置"""
        if launch_args_config:
            self.listen_addr_lineedit.setText(launch_args_config.get('Listen', '127.0.0.1'))
            self.port_lineedit.setText(launch_args_config.get('Port', '8188'))

            self.other_args_lineedit.setText(launch_args_config.get('Other', ''))
