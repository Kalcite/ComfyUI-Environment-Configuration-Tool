# ui/tab_venv.py
import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, 
    QLabel, QTextEdit, QMessageBox, QListWidget, QRadioButton, QGroupBox, 
    QStackedWidget, QListWidgetItem
)
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QTextCursor

# 从主窗口导入常量
# 延迟导入避免初始化问题（已解决）
# from main_app import Tsinghua_Mirror, AMD_TORCH_WHEELS

class TabVenv(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        # 进程1:Tab3
        self.install_process = QProcess(self)
        self.install_process.readyReadStandardOutput.connect(self.handle_qprocess_stdout)
        self.install_process.readyReadStandardError.connect(self.handle_qprocess_stderr)
        self.install_process.finished.connect(self.handle_qprocess_finished)
        
        # 安装队列
        self.install_queue = []
        self.current_venv_path_in_creation = ""
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 选项组
        self.radio_group = QGroupBox("Venv 模式 (二选一)")
        radio_layout = QHBoxLayout()
        self.radio_manual = QRadioButton("1. 手动选择已有 Venv")
        self.radio_auto = QRadioButton("2. 自动创建新 Venv (推荐)")
        radio_layout.addWidget(self.radio_manual)
        radio_layout.addWidget(self.radio_auto)
        self.radio_group.setLayout(radio_layout)
        layout.addWidget(self.radio_group)

        # 堆叠窗口
        self.venv_stack = QStackedWidget()
        layout.addWidget(self.venv_stack)
        
        # 页面1: 手动
        page_manual = QWidget()
        manual_layout = QVBoxLayout(page_manual)
        manual_h_layout = QHBoxLayout()
        self.manual_venv_lineedit = QLineEdit()
        self.manual_venv_lineedit.setReadOnly(True)
        manual_h_layout.addWidget(QLabel("Venv 目录:"))
        manual_h_layout.addWidget(self.manual_venv_lineedit)
        manual_browse_btn = QPushButton("浏览...")
        manual_browse_btn.clicked.connect(self.select_manual_venv)
        manual_h_layout.addWidget(manual_browse_btn)
        manual_layout.addLayout(manual_h_layout)
        
        self.validate_venv_btn = QPushButton("验证 Python 版本 (必须为 3.12)")
        self.validate_venv_btn.clicked.connect(self.validate_manual_venv)
        manual_layout.addWidget(self.validate_venv_btn)
        self.manual_status_label = QLabel("状态: 未选择")
        manual_layout.addWidget(self.manual_status_label)
        manual_layout.addStretch()
        
        # 页面2: 自动
        page_auto = QWidget()
        auto_layout = QVBoxLayout(page_auto)
        auto_layout.addWidget(QLabel("<b>自动创建 (需要基于 Python 3.12)</b>"))
        auto_layout.addWidget(QLabel("请从下方选择一个 'Python 3.12.x' 解释器用于创建 Venv:"))
        self.auto_python_selector = QListWidget()
        self.auto_python_selector.setFixedHeight(100)
        auto_layout.addWidget(self.auto_python_selector)
        
        self.auto_create_venv_btn = QPushButton("开始创建 Venv 并安装 AMD-Torch (ROCm)")
        self.auto_create_venv_btn.clicked.connect(self.start_auto_create_venv)
        auto_layout.addWidget(self.auto_create_venv_btn)
        self.auto_status_label = QLabel("状态: 未创建")
        auto_layout.addWidget(self.auto_status_label)
        
        self.venv_stack.addWidget(page_manual)
        self.venv_stack.addWidget(page_auto)
        
        self.radio_manual.toggled.connect(self.switch_venv_mode)
        self.radio_auto.toggled.connect(self.switch_venv_mode)
        self.radio_auto.setChecked(True)
        
        layout.addWidget(QLabel("<b>安装日志:</b>"))
        self.venv_log_display = QTextEdit()
        self.venv_log_display.setReadOnly(True)
        layout.addWidget(self.venv_log_display)

    def set_controls_enabled(self, enabled):
        """供外部 (如 Tab 6) 调用的方法，用于启用/禁用安装按钮"""
        self.radio_group.setEnabled(enabled)
        self.validate_venv_btn.setEnabled(enabled)
        self.auto_create_venv_btn.setEnabled(enabled)

    def set_installation_in_progress(self, in_progress):
        """设置UI为“安装中”状态，禁用所有其他操作"""
        enabled = not in_progress
        # 1. 禁用/启用所有Tabs
        self.main_window.tabs.setEnabled(enabled)
        # 2. 启用/禁用 Tab 3 自己的按钮
        self.set_controls_enabled(enabled)
        # 3. 禁用/启用 Tab 6 (启动) 的按钮
        if hasattr(self.main_window, 'tab6'):
            self.main_window.tab6.set_controls_enabled(enabled)

    def switch_venv_mode(self):
        if self.radio_manual.isChecked():
            self.venv_stack.setCurrentIndex(0)
            self.radio_auto.setEnabled(True)
            self.radio_manual.setEnabled(False)
            self.auto_status_label.setText("状态: 未创建")
            self.auto_status_label.setStyleSheet("color: gray;")
        else:
            self.venv_stack.setCurrentIndex(1)
            self.radio_manual.setEnabled(True)
            self.radio_auto.setEnabled(False)
            self.manual_status_label.setText("状态: 未选择")
            self.manual_status_label.setStyleSheet("color: gray;")
    
    def update_tab3_python_selector(self):
        """由 Tab 1 调用的回调函数"""
        self.auto_python_selector.clear()
        found_312 = False
        for path, version in self.main_window.python_interpreters.items(): # 读取共享变量
            if "3.12" in version:
                item = QListWidgetItem(f"{version} | {path}")
                item.setData(Qt.UserRole, path)
                self.auto_python_selector.addItem(item)
                found_312 = True
        
        if not found_312:
            self.auto_python_selector.addItem("未找到 Python 3.12，请先安装。")
            self.auto_create_venv_btn.setEnabled(False)
        else:
            self.auto_python_selector.setCurrentRow(0)
            self.auto_create_venv_btn.setEnabled(True)

    def select_manual_venv(self):
        directory = QFileDialog.getExistingDirectory(self, "选择 Venv 目录")
        if directory:
            python_exe = os.path.join(directory, 'Scripts', 'python.exe')
            if os.path.exists(python_exe):
                self.manual_venv_lineedit.setText(directory)
                self.manual_status_label.setText("状态: 找到 'Scripts/python.exe'，请验证版本。")
                self.manual_status_label.setStyleSheet("color: blue;")
            else:
                QMessageBox.warning(self, "路径无效", "未找到 'Scripts/python.exe'。请选择 Venv 根目录。")

    def validate_manual_venv(self):
        venv_path = self.manual_venv_lineedit.text()
        if not venv_path:
            QMessageBox.warning(self, "错误", "请先选择一个 Venv 目录。")
            return
            
        python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
        try:
            output = subprocess.check_output(
                [python_exe, '-c', "import sys; print(sys.version)"], 
                stderr=subprocess.STDOUT
            ).decode('utf-8')
            
            self.venv_log_display.setText(f"--- 验证Venv: {venv_path} ---\n{output}")
            
            if "3.12" in output:
                QMessageBox.information(self, "验证成功", f"版本匹配 (Python 3.12)。\nVenv 路径已锁定。")
                self.main_window.venv_dir = venv_path # 更新共享变量
                self.manual_status_label.setText(f"状态: [锁定] Python 3.12 venv 已确认。")
                self.manual_status_label.setStyleSheet("color: green;")
                self.main_window.save_config() # 调用主窗口保存
            else:
                QMessageBox.warning(self, "验证失败", f"该 Venv 的 Python 版本不匹配。\n需要: 3.12\n检测到: {output.split(' ')[0]}")
                self.manual_status_label.setText("状态: Python 版本不匹配 (非 3.12)")
                self.manual_status_label.setStyleSheet("color: red;")
                
        except Exception as e:
            QMessageBox.critical(self, "执行错误", f"无法执行 'python.exe':\n{e}")
            self.venv_log_display.append(f"[错误] {e}")

    def start_auto_create_venv(self):
        # 0. 检查 Project Dir
        if not self.main_window.project_dir: # 读取共享变量
            QMessageBox.warning(self, "缺少步骤", "请先在 [二、项目路径] 选项卡中设置 ComfyUI 目录。")
            self.main_window.tabs.setCurrentIndex(1)
            return
            
        selected_item = self.auto_python_selector.currentItem()
        if not selected_item or not selected_item.data(Qt.UserRole):
             QMessageBox.warning(self, "缺少 Python", "请先在列表中选择一个 Python 3.12 解释器。")
             return
        
        base_python_exe = selected_item.data(Qt.UserRole)
        
        self.current_venv_path_in_creation = os.path.join(os.getcwd(), "comfyui_amd_venv")
        venv_python_exe = os.path.join(self.current_venv_path_in_creation, 'Scripts', 'python.exe')
        comfy_req_txt = os.path.join(self.main_window.project_dir, 'requirements.txt')
        
        from main_app import Tsinghua_Mirror, AMD_TORCH_WHEELS

        self.venv_log_display.clear()
        self.set_installation_in_progress(True) # 锁定UI
        self.log_output(f"将在 '{self.current_venv_path_in_creation}' 创建 Venv...")
        self.log_output(f"使用基础 Python: {base_python_exe}\n")
        self.auto_status_label.setText("状态: 正在创建 Venv...")

        # self.install_queue = [
        #     (base_python_exe, ['-m', 'venv', self.current_venv_path_in_creation]),
        #     (venv_python_exe, ['-m', 'pip', 'install', '--upgrade', 'pip', '-i', Tsinghua_Mirror]),
        #     (venv_python_exe, ['install', '--no-cache-dir', AMD_TORCH_WHEELS[0], '-i', Tsinghua_Mirror]),
        #     (venv_python_exe, ['install', '--no-cache-dir', AMD_TORCH_WHEELS[1], '-i', Tsinghua_Mirror]),
        #     (venv_python_exe, ['install', '--no-cache-dir', AMD_TORCH_WHEELS[2], '-i', Tsinghua_Mirror]),
        #     (venv_python_exe, ['install', '-r', comfy_req_txt, '-i', Tsinghua_Mirror])
        # ]
        
        self.install_queue = [
            (base_python_exe, ['-m', 'venv', self.current_venv_path_in_creation]),
            (venv_python_exe, ['-m', 'pip', 'install', '--upgrade', 'pip', '-i', Tsinghua_Mirror]),
            (venv_python_exe, ['-m', 'pip', 'install', '--no-cache-dir', AMD_TORCH_WHEELS[0], '-i', Tsinghua_Mirror]),
            (venv_python_exe, ['-m', 'pip', 'install', '--no-cache-dir', AMD_TORCH_WHEELS[1], '-i', Tsinghua_Mirror]),
            (venv_python_exe, ['-m', 'pip', 'install', '--no-cache-dir', AMD_TORCH_WHEELS[2], '-i', Tsinghua_Mirror]),
            (venv_python_exe, ['-m', 'pip', 'install', '-r', comfy_req_txt, '-i', Tsinghua_Mirror])
        ]
        
        self.run_next_install_command()

    def run_next_install_command(self):
        if self.install_queue:
            cmd, args = self.install_queue.pop(0)
            
            if 'venv' in ' '.join(args):
                self.auto_status_label.setText("状态: 1/4 - 正在创建 Venv...")
            elif 'upgrade' in ' '.join(args):
                self.auto_status_label.setText("状态: 2/4 - 正在更新 Pip...")
            elif 'torch' in ' '.join(args):
                self.auto_status_label.setText("状态: 3/4 - 正在安装 AMD-Torch (ROCm)...")
            elif 'requirements.txt' in ' '.join(args):
                self.auto_status_label.setText("状态: 4/4 - 正在安装 ComfyUI 依赖...")

            self.log_output(f"\n--- [执行] ---\n{cmd} {' '.join(args)}\n")
            self.install_process.start(cmd, args)
        
    def handle_qprocess_finished(self, exitCode, exitStatus):
        if self.sender() != self.install_process:
            return
            
        if exitStatus == QProcess.CrashExit or exitCode != 0:
            self.log_output(f"\n--- [错误] ---")
            self.log_output(f"上一步执行失败！退出代码: {exitCode}")
            self.log_output("安装已停止。请检查错误信息、网络连接或 Python 3.12 环境。")
            self.set_installation_in_progress(False) # 解锁UI
            self.install_queue.clear() 
            self.auto_status_label.setText("状态: 安装失败！")
            self.auto_status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "安装失败", "环境安装过程中发生错误，请检查日志。")
        else:
            if self.install_queue:
                self.run_next_install_command()
            else:
                # 队列完成
                self.log_output("\n--- [成功] ---")
                self.log_output("所有环境已安装完毕！")
                self.set_installation_in_progress(False) # 解锁UI
                
                self.main_window.venv_dir = self.current_venv_path_in_creation # 更新共享变量
                self.auto_status_label.setText(f"状态: [锁定] Venv 创建成功并已保存。")
                self.auto_status_label.setStyleSheet("color: green;")
                self.main_window.save_config() # 调用主窗口保存
                QMessageBox.information(self, "成功", f"Venv 已在 '{self.main_window.venv_dir}' 成功创建并配置。")

    def log_output(self, text):
        self.venv_log_display.moveCursor(QTextCursor.End)
        self.venv_log_display.insertPlainText(text + "\n")
        self.venv_log_display.moveCursor(QTextCursor.End)

    def handle_qprocess_stdout(self):
        data = self.install_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.venv_log_display.moveCursor(QTextCursor.End)
        self.venv_log_display.insertPlainText(data)

    def handle_qprocess_stderr(self):
        data = self.install_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.venv_log_display.moveCursor(QTextCursor.End)
        self.venv_log_display.insertPlainText(f"[错误流] {data}")

    def update_ui_from_config(self, venv_dir):
        """由 main_app 调用，用于在启动时加载配置"""
        if venv_dir:
            self.radio_manual.setChecked(True)
            self.manual_venv_lineedit.setText(venv_dir)
            self.manual_status_label.setText("状态: [已加载] Venv 路径已锁定。")
            self.manual_status_label.setStyleSheet("color: green;")