# ui/tab_rocm_check.py
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget

class TabRocmCheck(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.initUI()
        self.refresh_tab4_rocm() # 启动时自动刷新

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>ROCm (HIP SDK) 安装检测:</b>"))
        layout.addWidget(QLabel(f"默认查找路径: 'C:\\Program Files\\AMD\\ROCm'"))
        
        self.rocm_list_widget = QListWidget()
        self.rocm_list_widget.setFixedHeight(150)
        layout.addWidget(self.rocm_list_widget)
        
        self.rocm_status_label = QLabel(
            '<b>状态: </b> 需要rocm版本 ≥ 6.2.4 (推荐 6.4.4)。<br>'
            '如果未安装或版本过低，请访问: '
            '<a href="https://www.amd.com/zh-cn/developer/resources/rocm-hub/hip-sdk.html">HIP SDK 官方下载</a>'
        )
        self.rocm_status_label.setOpenExternalLinks(True)
        layout.addWidget(self.rocm_status_label)
        
        refresh_btn = QPushButton("刷新 ROCm 检测")
        refresh_btn.clicked.connect(self.refresh_tab4_rocm)
        layout.addWidget(refresh_btn)
        layout.addStretch()

    def refresh_tab4_rocm(self):
        self.rocm_list_widget.clear()
        rocm_path = r"C:\Program Files\AMD\ROCm"
        if os.path.exists(rocm_path):
            try:
                versions = [d for d in os.listdir(rocm_path) if os.path.isdir(os.path.join(rocm_path, d))]
                if versions:
                    self.rocm_list_widget.addItem("检测到以下 ROCm (HIP SDK) 版本目录:")
                    for version in versions:
                        self.rocm_list_widget.addItem(f"- {version}")
                else:
                    self.rocm_list_widget.addItem("找到 ROCm 目录，但内部没有版本文件夹。")
            except Exception as e:
                self.rocm_list_widget.addItem(f"读取 ROCm 目录失败: {e}")
        else:
            self.rocm_list_widget.addItem("[警告] 未找到 ROCm (HIP SDK) 安装目录。")
            self.rocm_list_widget.addItem("请确保已安装 HIP SDK。")