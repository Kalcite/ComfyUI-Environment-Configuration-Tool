# plugins/nvidia_support.py
import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QFileDialog, 
    QLabel, QTextEdit, QMessageBox, QListWidget, QRadioButton, 
    QGroupBox, QComboBox, QListWidgetItem, QStackedWidget, QHBoxLayout
)
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QTextCursor

# --- [新] PyTorch (NVIDIA) 版本定义 ---
# 根据torch_version.txt列表(预定)
TORCH_CUDA_VERSIONS = [
    {'name': 'PyTorch 2.8.0 (CUDA 12.6)', 'cuda_key': 'cu126', 'packages': ['torch==2.8.0', 'torchvision==0.23.0', 'torchaudio==2.8.0']},
    {'name': 'PyTorch 2.8.0 (CUDA 12.8)', 'cuda_key': 'cu128', 'packages': ['torch==2.8.0', 'torchvision==0.23.0', 'torchaudio==2.8.0']},
    {'name': 'PyTorch 2.8.0 (CUDA 12.9)', 'cuda_key': 'cu129', 'packages': ['torch==2.8.0', 'torchvision==0.23.0', 'torchaudio==2.8.0']},
    {'name': 'PyTorch 2.7.1 (CUDA 11.8)', 'cuda_key': 'cu118', 'packages': ['torch==2.7.1', 'torchvision==0.22.1', 'torchaudio==2.7.1']},
    {'name': 'PyTorch 2.7.1 (CUDA 12.6)', 'cuda_key': 'cu126', 'packages': ['torch==2.7.1', 'torchvision==0.22.1', 'torchaudio==2.7.1']},
    {'name': 'PyTorch 2.7.1 (CUDA 12.8)', 'cuda_key': 'cu128', 'packages': ['torch==2.7.1', 'torchvision==0.22.1', 'torchaudio==2.7.1']},
    {'name': 'PyTorch 2.7.0 (CUDA 11.8)', 'cuda_key': 'cu118', 'packages': ['torch==2.7.0', 'torchvision==0.22.0', 'torchaudio==2.7.0']},
    {'name': 'PyTorch 2.7.0 (CUDA 12.6)', 'cuda_key': 'cu126', 'packages': ['torch==2.7.0', 'torchvision==0.22.0', 'torchaudio==2.7.0']},
    {'name': 'PyTorch 2.7.0 (CUDA 12.8)', 'cuda_key': 'cu128', 'packages': ['torch==2.7.0', 'torchvision==0.22.0', 'torchaudio==2.7.0']},
    {'name': 'PyTorch 2.6.0 (CUDA 11.8)', 'cuda_key': 'cu118', 'packages': ['torch==2.6.0', 'torchvision==0.21.0', 'torchaudio==2.6.0']},
    {'name': 'PyTorch 2.6.0 (CUDA 12.4)', 'cuda_key': 'cu124', 'packages': ['torch==2.6.0', 'torchvision==0.21.0', 'torchaudio==2.6.0']},
    {'name': 'PyTorch 2.6.0 (CUDA 12.6)', 'cuda_key': 'cu126', 'packages': ['torch==2.6.0', 'torchvision==0.21.0', 'torchaudio==2.6.0']},
    {'name': 'PyTorch 2.5.1 (CUDA 11.8)', 'cuda_key': 'cu118', 'packages': ['torch==2.5.1', 'torchvision==0.20.1', 'torchaudio==2.5.1']},
    {'name': 'PyTorch 2.5.1 (CUDA 12.1)', 'cuda_key': 'cu121', 'packages': ['torch==2.5.1', 'torchvision==0.20.1', 'torchaudio==2.5.1']},
    {'name': 'PyTorch 2.5.1 (CUDA 12.4)', 'cuda_key': 'cu124', 'packages': ['torch==2.5.1', 'torchvision==0.20.1', 'torchaudio==2.5.1']},
]

# --- 插件全局变量 (用于保存原始Tab) ---
original_state = {}


def register(main_window):
    # 
    # 注册 'NVIDIA Support' 插件。
    # 这将 *替换* Tab 3 并 *禁用* Tab 4。
    # 
    print("[Plugin: NVIDIA Support] 正在注册...")
    global original_state
    
    try:
        # 1. 保存并移除原始的 Tab 3 (AMD Venv)
        original_state['tab3_widget'] = main_window.tab3
        original_state['tab3_index'] = main_window.tabs.indexOf(main_window.tab3)
        original_state['tab3_text'] = main_window.tabs.tabText(original_state['tab3_index'])
        main_window.tabs.removeTab(original_state['tab3_index'])
        
        # 2. 创建并插入新的 Tab 3 (NVIDIA Venv)
        main_window.nvidia_tab = TabNvidiaVenv(main_window)
        main_window.tabs.insertTab(original_state['tab3_index'], main_window.nvidia_tab, "3 虚拟环境 (NVIDIA)")
        # 更新主窗口对 Tab 3 的引用 (!!!)
        main_window.tab3 = main_window.nvidia_tab 
        
        # 3. 禁用 Tab 4 (ROCm)
        original_state['tab4_widget'] = main_window.tab4
        original_state['tab4_index'] = main_window.tabs.indexOf(main_window.tab4)
        original_state['tab4_text'] = main_window.tabs.tabText(original_state['tab4_index'])
        main_window.tabs.setTabEnabled(original_state['tab4_index'], False)
        main_window.tabs.setTabText(original_state['tab4_index'], "4 ROCm (不可用)")
        
        # 4. 加载 NVIDIA Venv 路径
        main_window.tab3.update_ui_from_config(main_window.venv_dir_nv)
        # 5. 刷新 python 列表
        main_window.tab3.update_tab3_python_selector()

        print("[Plugin: NVIDIA Support] 注册完成。Tab 3 已替换, Tab 4 已禁用。")
        
    except Exception as e:
        print(f"[Plugin: NVIDIA Support] 注册失败: {e}")
        import traceback
        traceback.print_exc()

def unregister(main_window):
    # 
    # 卸载 'NVIDIA Support' 插件。
    # 恢复原始的 Tab 3 (AMD) 和 Tab 4 (ROCm)。
    # 
    print("[Plugin: NVIDIA Support] 正在卸载...")
    global original_state
    
    try:
        # 1. 移除 Tab 3 (NVIDIA Venv)
        main_window.tabs.removeTab(main_window.tabs.indexOf(main_window.nvidia_tab))
        
        # 2. 恢复原始 Tab 3 (AMD Venv)
        main_window.tabs.insertTab(original_state['tab3_index'], original_state['tab3_widget'], original_state['tab3_text'])
        # 恢复主窗口对 Tab 3 的引用 (!!!)
        main_window.tab3 = original_state['tab3_widget'] 
        
        # 3. 恢复 Tab 4 (ROCm)
        main_window.tabs.setTabEnabled(original_state['tab4_index'], True)
        main_window.tabs.setTabText(original_state['tab4_index'], original_state['tab4_text'])
        
        # 4. 加载 AMD Venv 路径
        main_window.tab3.update_ui_from_config(main_window.venv_dir)

        print("[Plugin: NVIDIA Support] 卸载完成。Tab 3 和 Tab 4 已恢复。")
    except Exception as e:
        print(f"[Plugin: NVIDIA Support] 卸载失败: {e}")

    original_state.clear()


# ======================================================================
#  NVIDIA VENV TAB WIDGET
#  独立的 QWidget 类，tab_venv.py 的 NVIDIA 定制版
# ======================================================================

class TabNvidiaVenv(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.install_process = QProcess(self)
        self.install_process.readyReadStandardOutput.connect(self.handle_qprocess_stdout)
        self.install_process.readyReadStandardError.connect(self.handle_qprocess_stderr)
        self.install_process.finished.connect(self.handle_qprocess_finished)
        
        self.install_queue = []
        self.current_venv_path_in_creation = ""
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        # --- 模式选择 ---
        self.radio_group = QGroupBox("Venv 模式 (二选一)")
        radio_layout = QHBoxLayout()
        self.radio_manual = QRadioButton("1. 手动选择已有 Venv (NVIDIA)")
        self.radio_auto = QRadioButton("2. 自动创建新 Venv (NVIDIA)")
        radio_layout.addWidget(self.radio_manual)
        radio_layout.addWidget(self.radio_auto)
        self.radio_group.setLayout(radio_layout)
        layout.addWidget(self.radio_group)

        self.venv_stack = QStackedWidget()
        layout.addWidget(self.venv_stack)
        
        # --- 页面1: 手动 ---
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
        
        # --- 页面2: 自动 ---
        page_auto = QWidget()
        auto_layout = QVBoxLayout(page_auto)
        
        auto_layout.addWidget(QLabel("<b>自动创建 (需要基于 Python 3.12)</b>"))
        auto_layout.addWidget(QLabel("请从下方选择一个 'Python 3.12.x' 解释器:"))
        self.auto_python_selector = QListWidget()
        self.auto_python_selector.setFixedHeight(100)
        auto_layout.addWidget(self.auto_python_selector)
        
        # --- NVIDIA 特有 UI ---
        auto_layout.addWidget(QLabel("<b>1. 选择 PyTorch (CUDA/CPU) 版本:</b>"))
        self.nv_torch_selector = QComboBox()
        for version_data in TORCH_CUDA_VERSIONS:
            self.nv_torch_selector.addItem(version_data['name'], userData=version_data)
        auto_layout.addWidget(self.nv_torch_selector)
            
        auto_layout.addWidget(QLabel("<b>2. 选择下载源:</b>"))
        self.nv_source_group = QGroupBox()
        source_layout = QVBoxLayout()
        self.nv_radio_pytorch = QRadioButton("PyTorch 官方源 (推荐, 速度可能较慢)")
        self.nv_radio_tsinghua = QRadioButton("CPU模式(无需参考cuda版本，搭配--cpu参数使用)")
        self.nv_radio_pytorch.setChecked(True) # 默认官方
        source_layout.addWidget(self.nv_radio_pytorch)
        source_layout.addWidget(self.nv_radio_tsinghua)
        self.nv_source_group.setLayout(source_layout)
        auto_layout.addWidget(self.nv_source_group)
        self.help_text_edit = QTextEdit(self)
        self.help_text_edit.setReadOnly(True)
        self.help_text_edit.setMaximumHeight(100)
        
        help_text = (
            "cpu模式的环境与NV环境重名，若想保留请重命名虚拟环境目录comfyui_nv_venv为comfyui_cpu_venv\n"
            "尽量在自动安装后选择手动配置环境\n"

        )
        self.help_text_edit.setText(help_text)
        layout.addWidget(self.help_text_edit)
        # --- NVIDIA UI 结束 ---
        
        self.auto_create_venv_btn = QPushButton("开始创建 Venv 环境")
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

    # --- 外部控制方法 ---
    def set_controls_enabled(self, enabled):
        self.radio_group.setEnabled(enabled)
        self.validate_venv_btn.setEnabled(enabled)
        self.auto_create_venv_btn.setEnabled(enabled)

    def set_installation_in_progress(self, in_progress):
        enabled = not in_progress
        self.main_window.tabs.setEnabled(enabled)
        self.set_controls_enabled(enabled)
        if hasattr(self.main_window, 'tab6'):
            self.main_window.tab6.set_controls_enabled(enabled)

    # --- UI 逻辑 ---
    def switch_venv_mode(self):
        if self.radio_manual.isChecked():
            self.venv_stack.setCurrentIndex(0)
        else:
            self.venv_stack.setCurrentIndex(1)
    
    def update_tab3_python_selector(self):
        """由 Tab 1 或插件加载时调用"""
        self.auto_python_selector.clear()
        found_312 = False
        for path, version in self.main_window.python_interpreters.items():
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

    # --- VENV 核心逻辑 (NVIDIA 版本) ---
    def select_manual_venv(self):
        directory = QFileDialog.getExistingDirectory(self, "选择 Venv 目录")
        if directory:
            python_exe = os.path.join(directory, 'Scripts', 'python.exe')
            if os.path.exists(python_exe):
                self.manual_venv_lineedit.setText(directory)
                self.manual_status_label.setText("状态: 找到 'Scripts/python.exe'，请验证版本。")
            else:
                QMessageBox.warning(self, "路径无效", "未找到 'Scripts/python.exe'。")

    def validate_manual_venv(self):
        venv_path = self.manual_venv_lineedit.text()
        if not venv_path: return
            
        python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
        try:
            output = subprocess.check_output(
                [python_exe, '-c', "import sys; print(sys.version)"], 
                stderr=subprocess.STDOUT
            ).decode('utf-8')
            
            self.venv_log_display.setText(f"--- 验证Venv: {venv_path} ---\n{output}")
            
            if "3.12" in output:
                QMessageBox.information(self, "验证成功", f"版本匹配 (Python 3.12)。\nVenv (NVIDIA) 路径已锁定。")
                self.main_window.venv_dir_nv = venv_path # [NVIDIA] 保存到 venv_dir_nv
                self.manual_status_label.setText(f"状态: [锁定] Python 3.12 venv (NVIDIA) 已确认。")
                self.manual_status_label.setStyleSheet("color: green;")
                self.main_window.save_config()
            else:
                QMessageBox.warning(self, "验证失败", f"该 Venv 的 Python 版本不匹配。")
                self.manual_status_label.setText("状态: Python 版本不匹配 (非 3.12)")
                
        except Exception as e:
            QMessageBox.critical(self, "执行错误", f"无法执行 'python.exe':\n{e}")

    def start_auto_create_venv(self):
        
        
        # 0. 检查
        if not self.main_window.project_dir:
            QMessageBox.warning(self, "缺少步骤", "请先在 [二、项目路径] 选项卡中设置 ComfyUI 目录。")
            self.main_window.tabs.setCurrentIndex(1)
            return
            
        selected_item = self.auto_python_selector.currentItem()
        if not selected_item or not selected_item.data(Qt.UserRole):
             QMessageBox.warning(self, "缺少 Python", "请先在列表中选择一个 Python 3.12 解释器。")
             return
        
        base_python_exe = selected_item.data(Qt.UserRole)
        
        # 1. [NVIDIA] 获取特定逻辑
        torch_data = self.nv_torch_selector.currentData()
        torch_packages = torch_data['packages']
        
        # 2. [NVIDIA] 设定 Venv 路径
        self.current_venv_path_in_creation = os.path.join(os.getcwd(), "comfyui_nv_venv") # [NVIDIA] 路径
        venv_python_exe = os.path.join(self.current_venv_path_in_creation, 'Scripts', 'python.exe')
        comfy_req_txt = os.path.join(self.main_window.project_dir, 'requirements.txt')

        # 3. [NVIDIA] 构建 pip 命令
        pip_install_cmd = [venv_python_exe, '-m', 'pip', 'install']
        
        # 试图从 main_window 获取镜像地址；若没有则延迟导入 main_app 常量；最后使用默认值
        mirror = getattr(self.main_window, 'Tsinghua_Mirror', None)
        if not mirror:
            try:
                from main_app import Tsinghua_Mirror as mirror
            except Exception:
                mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"

        
        if self.nv_radio_pytorch.isChecked():
            index_url = f"https://download.pytorch.org/whl/{torch_data['cuda_key']}"
            pip_torch_cmd = pip_install_cmd + torch_packages + ['--index-url', index_url]
        else:
            # pip_torch_cmd = pip_install_cmd + torch_packages + ['-i', self.main_window.Tsinghua_Mirror]
            pip_torch_cmd = pip_install_cmd + torch_packages + ['-i', mirror]
 

        # 4. 设置UI并清空日志
        self.venv_log_display.clear()
        self.set_installation_in_progress(True)
        self.log_output(f"[NVIDIA 模式] 将在 '{self.current_venv_path_in_creation}' 创建 Venv...")
        self.log_output(f"使用基础 Python: {base_python_exe}\n")
        self.auto_status_label.setText("状态: 正在创建 Venv...")

        # 5. [NVIDIA] 创建安装命令队列
        self.install_queue = [
            (base_python_exe, ['-m', 'venv', self.current_venv_path_in_creation]),
            # (venv_python_exe, ['-m', 'pip', 'install', '--upgrade', 'pip', '-i', self.main_window.Tsinghua_Mirror]),
            # (pip_torch_cmd[0], pip_torch_cmd[1:]), # [NVIDIA] Torch 命令
            # (venv_python_exe, ['-m', 'pip', 'install', '-r', comfy_req_txt, '-i', self.main_window.Tsinghua_Mirror])
            (venv_python_exe, ['-m', 'pip', 'install', '--upgrade', 'pip', '-i', mirror]),
            (pip_torch_cmd[0], pip_torch_cmd[1:]), # [NVIDIA] Torch 命令
            (venv_python_exe, ['-m', 'pip', 'install', '-r', comfy_req_txt, '-i', mirror])
        ]
        
        self.run_next_install_command()

    def run_next_install_command(self):
        if self.install_queue:
            cmd, args = self.install_queue.pop(0)
            
            # (状态标签可以保持和 AMD 一致)
            if 'venv' in ' '.join(args):
                self.auto_status_label.setText("状态: 1/4 - 正在创建 Venv...")
            elif 'upgrade' in ' '.join(args):
                self.auto_status_label.setText("状态: 2/4 - 正在更新 Pip...")
            elif 'torch' in ' '.join(args):
                self.auto_status_label.setText("状态: 3/4 - 正在安装 NVIDIA-Torch (CUDA)...")
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
            self.set_installation_in_progress(False)
            self.install_queue.clear() 
            self.auto_status_label.setText("状态: 安装失败！")
            QMessageBox.critical(self, "安装失败", "环境安装过程中发生错误，请检查日志。")
        else:
            if self.install_queue:
                self.run_next_install_command()
            else:
                # 队列完成
                self.log_output("\n--- [成功] ---")
                self.log_output("[NVIDIA 模式] 所有环境已安装完毕！")
                self.set_installation_in_progress(False)
                
                self.main_window.venv_dir_nv = self.current_venv_path_in_creation # [NVIDIA] 保存到 venv_dir_nv
                self.auto_status_label.setText(f"状态: [锁定] Venv (NVIDIA) 创建成功。")
                self.auto_status_label.setStyleSheet("color: green;")
                self.main_window.save_config()
                QMessageBox.information(self, "成功", f"Venv (NVIDIA) 已在 '{self.main_window.venv_dir_nv}' 成功创建。")

    # --- 日志和配置加载 ---
    def log_output(self, text):
        self.venv_log_display.moveCursor(QTextCursor.End)
        self.venv_log_display.insertPlainText(text + "\n")

    def handle_qprocess_stdout(self):
        data = self.install_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.venv_log_display.moveCursor(QTextCursor.End)
        self.venv_log_display.insertPlainText(data)

    def handle_qprocess_stderr(self):
        data = self.install_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.venv_log_display.moveCursor(QTextCursor.End)
        self.venv_log_display.insertPlainText(f"[错误流] {data}")

    def update_ui_from_config(self, venv_dir_nv):
        # 由 main_app 或 register 调用，用于在启动时加载配置
        if venv_dir_nv:
            self.radio_manual.setChecked(True)
            self.manual_venv_lineedit.setText(venv_dir_nv)
            self.manual_status_label.setText("状态: [已加载] Venv (NVIDIA) 路径已锁定。")
            self.manual_status_label.setStyleSheet("color: green;")
        else:
            self.radio_auto.setChecked(True)