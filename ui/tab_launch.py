# ui/tab_launch.py
import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox, QApplication
)
from PyQt5.QtCore import QProcess, QProcessEnvironment
from PyQt5.QtGui import QTextCursor

class TabLaunch(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        # 进程2:Tab6 
        self.launch_process = QProcess(self)
        self.launch_process.readyReadStandardOutput.connect(self.handle_launch_stdout)
        self.launch_process.readyReadStandardError.connect(self.handle_launch_stderr)
        self.launch_process.finished.connect(self.handle_launch_finished)
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        btn_layout = QHBoxLayout()
        self.launch_button = QPushButton("启动 ComfyUI")
        self.launch_button.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #4CAF50; color: white;")
        self.launch_button.clicked.connect(self.launch_comfyui)
        
        self.stop_button = QPushButton("停止 ComfyUI")
        self.stop_button.setStyleSheet("font-size: 16px; background-color: #f44336; color: white;")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_comfyui)
        
        btn_layout.addWidget(self.launch_button)
        btn_layout.addWidget(self.stop_button)
        layout.addLayout(btn_layout)
        
        layout.addWidget(QLabel("<b>ComfyUI 运行日志:</b>"))
        self.launch_log_display = QTextEdit()
        self.launch_log_display.setReadOnly(True)
        self.launch_log_display.setStyleSheet("background-color: #000; color: #FFF; font-family: 'Consolas', 'Courier New', monospace;")
        layout.addWidget(self.launch_log_display)

    def set_controls_enabled(self, enabled):
        # 供外部 (如 Tab 3) 调用的方法，用于启用/禁用启动按钮
        self.launch_button.setEnabled(enabled)
        # Stop 按钮的状态由 launch_process 自己的状态管理，不受外部影响
        
    

    def launch_comfyui(self):
        # 1. 验证路径 (读取共享变量)
        if not self.main_window.project_dir or not os.path.exists(self.main_window.project_dir):
            QMessageBox.warning(self, "启动失败", "ComfyUI 项目路径未设置或无效。")
            self.main_window.tabs.setCurrentIndex(1) # 跳转到 Tab 2
            return
            
        # venv_python_exe = os.path.join(self.main_window.venv_dir, 'Scripts', 'python.exe')
        # if not self.main_window.venv_dir or not os.path.exists(venv_python_exe):
        #     QMessageBox.warning(self, "启动失败", "Venv 路径 (Tab 3) 未设置或无效。")
        #     self.main_window.tabs.setCurrentIndex(2) # 跳转到 Tab 3
        #     return
            
        # if self.launch_process.state() == QProcess.ProcessState.Running:
        #     QMessageBox.information(self, "提示", "ComfyUI 似乎已在运行中。")
        #     return
        
        
        venv_dir_to_use = ''
        env_mode = "未知"
        tab3 = getattr(self.main_window, 'tab3', None)

        # 2. 优先强制使用 Tab3 的手动选择（如果用户在 Tab3 选择了“手动”模式）
        if tab3 and hasattr(tab3, 'radio_manual') and tab3.radio_manual.isChecked():
            manual_path = getattr(tab3, 'manual_venv_lineedit', None)
            manual_dir = manual_path.text().strip() if manual_path else ''
            python_candidate = os.path.join(manual_dir, 'Scripts', 'python.exe')
            if manual_dir and os.path.exists(python_candidate):
                venv_dir_to_use = manual_dir
                env_mode = "手动选择"
            else:
                QMessageBox.warning(self, "启动失败", "已选择手动模式，但手动 Venv 路径无效或未设置。")
                self.main_window.tabs.setCurrentIndex(2)  # 跳转到 Tab 3
                return
        else:
            # 3. 非手动模式：优先使用 NVIDIA 插件提供的 venv_dir_nv（若存在且有效），否则使用默认 venv_dir
            venv_nv = getattr(self.main_window, 'venv_dir_nv', '') or ''
            if venv_nv and os.path.exists(os.path.join(venv_nv, 'Scripts', 'python.exe')):
                venv_dir_to_use = venv_nv
                env_mode = "NVIDIA"
            else:
                venv_default = getattr(self.main_window, 'venv_dir', '') or ''
                if venv_default and os.path.exists(os.path.join(venv_default, 'Scripts', 'python.exe')):
                    venv_dir_to_use = venv_default
                    env_mode = "ROCm/默认"

        if not venv_dir_to_use:
            QMessageBox.warning(self, "启动失败", "Venv 路径 (Tab 3) 未设置或无效。")
            self.main_window.tabs.setCurrentIndex(2)  # 跳转到 Tab 3
            return

        venv_python_exe = os.path.join(venv_dir_to_use, 'Scripts', 'python.exe')

        if self.launch_process.state() == QProcess.ProcessState.Running:
            QMessageBox.information(self, "提示", "ComfyUI 似乎已在运行中。")
            return
            
        # 4. 获取启动参数
        listen = self.main_window.tab5.get_listen_addr() or "127.0.0.1"
        port = self.main_window.tab5.get_port() or "8188"
        other_args_str = self.main_window.tab5.get_other_args()
        
        launch_args = ['main.py'] 
        if listen: launch_args.extend(['--listen', listen])
        if port: launch_args.extend(['--port', port])
        if other_args_str: launch_args.extend(other_args_str.split())
        
        

        # 5. 设置 UI
        # self.launch_log_display.clear()
        # self.launch_log_display.append("--- 正在启动 ComfyUI (ROCm) ---")
        # self.launch_button.setEnabled(False)
        # self.stop_button.setEnabled(True)
        # # --- 跨 Tab 通信 ---
        # # 运行时禁止安装
        # if hasattr(self.main_window, 'tab3'):
        #     self.main_window.tab3.set_controls_enabled(False) 
        self.launch_log_display.clear()
        self.launch_log_display.append(f"--- 启动模式: {env_mode} ---")
        self.launch_log_display.append(f"--- Venv 路径: {venv_dir_to_use} ---")

        # --- [修改] 新需求 1: 运行 collect_env ---
        try:
            self.launch_log_display.append("\n--- [1/2] 正在收集 Torch 环境信息... ---")
            # 强制 UI 刷新，显示 "正在收集..."
            QApplication.processEvents() 
            
            collect_env_cmd = [venv_python_exe, '-m', 'torch.utils.collect_env']
            
            # 同步运行并捕获输出
            output = subprocess.check_output(
                collect_env_cmd, 
                cwd=self.main_window.project_dir, 
                stderr=subprocess.STDOUT,
                text=True, # 自动解码为 utf-8
                encoding='utf-8',
                errors='ignore' # 忽略解码错误
            )
            
            self.launch_log_display.append(output)
            self.launch_log_display.append("--- [1/2] 环境信息收集完毕 ---\n")

        except subprocess.CalledProcessError as e:
            # 如果 'collect_env' 失败 (例如 Torch 未安装)
            self.launch_log_display.append(f"\n--- [错误] 无法运行 'torch.utils.collect_env' ---")
            self.launch_log_display.append(e.output)
            self.launch_log_display.append("--- 进程已停止 (请检查 Tab 3 的 Venv 配置) ---")
            return # 阻止 ComfyUI 启动
        except Exception as e:
            self.launch_log_display.append(f"\n--- [严重错误] collect_env 失败: {e} ---")
            return
        # ---  collect_env 结束 ---

        # 6. 设置 UI (第二部分)
        self.launch_log_display.append("--- [2/2] 正在启动 ComfyUI... ---")
        self.launch_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        if hasattr(self.main_window, 'tab3'):
            self.main_window.tab3.set_controls_enabled(False)



        # 7. 启动进程
        command = venv_python_exe
        args = launch_args
        
        process_env = QProcessEnvironment.systemEnvironment()
        # 检查系统PATH中是否有git
        git_executable = self.find_git_executable()
        if git_executable:
            process_env.insert("GIT_PYTHON_GIT_EXECUTABLE", git_executable)
        else:
            self.launch_log_display.append("[警告] 系统中未找到git可执行文件，GitPython可能会出现问题")
            
            # 设置 Git 代理环境变量
        if self.main_window.git_proxy_enabled:
            if self.main_window.git_http_proxy:
                process_env.insert("HTTP_PROXY", self.main_window.git_http_proxy)
                process_env.insert("http_proxy", self.main_window.git_http_proxy)
            if self.main_window.git_https_proxy:
                process_env.insert("HTTPS_PROXY", self.main_window.git_https_proxy)
                process_env.insert("https_proxy", self.main_window.git_https_proxy)

        self.launch_process.setProcessEnvironment(process_env)
        self.launch_process.setWorkingDirectory(self.main_window.project_dir) 

        # self.launch_process.setWorkingDirectory(self.main_window.project_dir)

        self.launch_log_display.append(f"[执行] {command} {' '.join(args)}")
        self.launch_log_display.append(f"[工作目录] {self.main_window.project_dir}\n")
        
        self.launch_process.start(command, args)
        
    

    def stop_comfyui(self):
        if self.launch_process.state() == QProcess.ProcessState.Running:
            self.launch_log_display.append("\n--- [用户操作] 发送停止信号... ---")
            self.launch_process.terminate() 
            if self.launch_process.waitForFinished(2000):
                self.launch_log_display.append("ComfyUI 进程已正常退出。")
            else:
                self.launch_log_display.append("进程未在 2 秒内退出，正在强制终止...")
                self.launch_process.kill()
        else:
            self.launch_log_display.append("\n--- [用户操作] 进程未在运行 ---")

    def handle_launch_stdout(self):
        data = self.launch_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.launch_log_display.moveCursor(QTextCursor.End)
        self.launch_log_display.insertPlainText(data)

    def handle_launch_stderr(self):
        data = self.launch_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.launch_log_display.moveCursor(QTextCursor.End)
        self.launch_log_display.insertPlainText(f"[STDERR] {data}") 

    def handle_launch_finished(self):
        self.launch_log_display.append("\n--- ComfyUI 进程已停止 ---")
        self.launch_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        # --- 跨 Tab 通信 ---
        # 恢复安装功能
        if hasattr(self.main_window, 'tab3'):
            self.main_window.tab3.set_controls_enabled(True)
            
    def find_git_executable(self):

    # 首先检查是否已经在环境变量中设置了GIT_PYTHON_GIT_EXECUTABLE
        git_executable = os.environ.get('GIT_PYTHON_GIT_EXECUTABLE')
        if git_executable and os.path.exists(git_executable):
            return git_executable
        
        # 在PATH中搜索git
        git_names = ['git.exe', 'git']
        for path_dir in os.environ.get('PATH', '').split(os.pathsep):
            for git_name in git_names:
                git_path = os.path.join(path_dir, git_name)
                if os.path.exists(git_path):
                    return git_path
        
        # Windows常见安装路径
        common_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
            r"C:\Git\bin\git.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        return None  # 如果没找到git可执行文件，返回None