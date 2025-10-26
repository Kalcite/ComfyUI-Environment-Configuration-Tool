# ui/tab_git_clone.py
import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, 
    QLabel, QTextEdit, QMessageBox, QGroupBox, QFormLayout, QCheckBox, QComboBox
)
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QTextCursor

class TabGitClone(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window 

        self.git_process = QProcess(self)
        self.git_process.readyReadStandardOutput.connect(self.handle_git_stdout)
        self.git_process.readyReadStandardError.connect(self.handle_git_stderr)
        self.git_process.finished.connect(self.handle_git_finished)

        self.initUI()
        self.auto_detect_git() 

    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Git 可执行文件路径设置
        git_group = QGroupBox("Git 可执行文件路径 (.exe)")
        git_layout = QHBoxLayout(git_group)
        
        self.git_path_lineedit = QLineEdit(self)
        self.git_path_lineedit.setReadOnly(True)
        git_layout.addWidget(self.git_path_lineedit)
        
        self.git_browse_btn = QPushButton("手动选择 git.exe")
        self.git_browse_btn.clicked.connect(self.select_git_exe)
        git_layout.addWidget(self.git_browse_btn)
        
        layout.addWidget(git_group)
        
        self.git_status_label = QLabel("状态: 正在检测 Git 安装...")
        self.git_status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.git_status_label)
        
        # Git 代理设置
        proxy_group = QGroupBox("Git 代理设置")
        proxy_layout = QFormLayout(proxy_group)
        
        self.proxy_enabled_checkbox = QCheckBox("启用 Git 代理")
        proxy_layout.addRow(self.proxy_enabled_checkbox)
        
        # HTTP 代理
        http_proxy_layout = QHBoxLayout()
        self.http_proxy_type = QComboBox()
        self.http_proxy_type.addItems(["http", "socks5"])
        self.http_proxy_type.setCurrentText("http")
        
        self.http_proxy_addr = QLineEdit()
        self.http_proxy_addr.setPlaceholderText("例如: 127.0.0.1")
        
        self.http_proxy_port = QLineEdit()
        self.http_proxy_port.setPlaceholderText("例如: 1080")
        self.http_proxy_port.setMaximumWidth(80)
        
        http_proxy_layout.addWidget(self.http_proxy_type)
        http_proxy_layout.addWidget(QLabel("://"))
        http_proxy_layout.addWidget(self.http_proxy_addr)
        http_proxy_layout.addWidget(QLabel(":"))
        http_proxy_layout.addWidget(self.http_proxy_port)
        
        proxy_layout.addRow("HTTP 代理:", http_proxy_layout)
        
        # HTTPS 代理
        https_proxy_layout = QHBoxLayout()
        self.https_proxy_type = QComboBox()
        self.https_proxy_type.addItems(["http", "socks5"])
        self.https_proxy_type.setCurrentText("http")
        
        self.https_proxy_addr = QLineEdit()
        self.https_proxy_addr.setPlaceholderText("例如: 127.0.0.1")
        
        self.https_proxy_port = QLineEdit()
        self.https_proxy_port.setPlaceholderText("例如: 1080")
        self.https_proxy_port.setMaximumWidth(80)
        
        https_proxy_layout.addWidget(self.https_proxy_type)
        https_proxy_layout.addWidget(QLabel("://"))
        https_proxy_layout.addWidget(self.https_proxy_addr)
        https_proxy_layout.addWidget(QLabel(":"))
        https_proxy_layout.addWidget(self.https_proxy_port)
        
        proxy_layout.addRow("HTTPS 代理:", https_proxy_layout)
        
        # 代理操作按钮
        proxy_btn_layout = QHBoxLayout()
        self.apply_proxy_btn = QPushButton("应用代理设置")
        self.apply_proxy_btn.clicked.connect(self.apply_git_proxy)
        self.unset_proxy_btn = QPushButton("取消代理设置")
        self.unset_proxy_btn.clicked.connect(self.unset_git_proxy)
        self.check_proxy_btn = QPushButton("查看当前设置")
        self.check_proxy_btn.clicked.connect(self.check_git_proxy)
        
        proxy_btn_layout.addWidget(self.apply_proxy_btn)
        proxy_btn_layout.addWidget(self.unset_proxy_btn)
        proxy_btn_layout.addWidget(self.check_proxy_btn)
        
        proxy_layout.addRow(proxy_btn_layout)
        
        layout.addWidget(proxy_group)
        
        # Git Clone 目标目录设置
        target_group = QGroupBox("Git Clone 目标目录")
        target_layout = QHBoxLayout(target_group)
        
        self.clone_target_lineedit = QLineEdit(self)
        self.clone_target_lineedit.setPlaceholderText("可选：手动指定目录，例如 D:\\NewComfyUI")
        target_layout.addWidget(self.clone_target_lineedit)
        
        self.clone_target_browse_btn = QPushButton("浏览...")
        self.clone_target_browse_btn.clicked.connect(self.select_clone_target_dir)
        target_layout.addWidget(self.clone_target_browse_btn)
        
        layout.addWidget(target_group)

        # ComfyUI 仓库克隆设置
        clone_group = QGroupBox("ComfyUI 仓库克隆")
        clone_layout = QVBoxLayout(clone_group)
        
        clone_layout.addWidget(QLabel("<b>目标 URL:</b> https://github.com/comfyanonymous/ComfyUI.git"))
        clone_layout.addWidget(QLabel(
            "<b>目标目录:</b> 优先使用上方手动指定的目录。若未指定，则使用 项目路径 中的项目目录。"
        ))
        
        self.clone_button = QPushButton("Git Clone ComfyUI 仓库")
        self.clone_button.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #2196F3; color: white;")
        self.clone_button.setEnabled(False) 
        self.clone_button.clicked.connect(self.clone_comfyui)
        clone_layout.addWidget(self.clone_button)
        
        layout.addWidget(clone_group)
        
        layout.addWidget(QLabel("<b>Git 操作日志:</b>"))
        self.git_log_display = QTextEdit()
        self.git_log_display.setReadOnly(True)
        self.git_log_display.setStyleSheet("background-color: #1a1a1a; color: #EEE;")
        layout.addWidget(self.git_log_display)
        
        layout.addStretch()

    def select_clone_target_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择 Git Clone 目标目录")
        if directory:
            self.clone_target_lineedit.setText(directory)

    def auto_detect_git(self):
        base_dir = os.getcwd()
        potential_git_paths = [
            os.path.join(base_dir, 'Git', 'bin', 'git.exe'),
            os.path.join(base_dir, 'git', 'bin', 'git.exe'),
        ]
        
        found_path = None
        for path in potential_git_paths:
            if os.path.exists(path):
                found_path = path
                break

        if not found_path:
            try:
                result = subprocess.check_output(['where', 'git']).decode('utf-8').strip().split('\r\n')
                if result and os.path.exists(result[0]):
                    found_path = result[0]
            except Exception:
                pass

        if found_path:
            self.main_window.git_exe_path = found_path # 更新共享变量
            self.git_path_lineedit.setText(self.main_window.git_exe_path)
            self.git_status_label.setText("状态: [自动检测] Git 路径已锁定。")
            self.git_status_label.setStyleSheet("color: green;")
            self.clone_button.setEnabled(True)
        else:
            self.git_status_label.setText("状态: [未找到] 请手动选择 'git.exe'。")
            self.git_status_label.setStyleSheet("color: red;")
            self.clone_button.setEnabled(False)

    def select_git_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 Git 可执行文件 (git.exe)", "", "Git Executable (git.exe)")
        if file_path and os.path.basename(file_path).lower() == 'git.exe':
            self.main_window.git_exe_path = file_path # 更新共享变量
            self.git_path_lineedit.setText(self.main_window.git_exe_path)
            self.git_status_label.setText("状态: [手动选择] Git 路径已锁定。")
            self.git_status_label.setStyleSheet("color: green;")
            self.clone_button.setEnabled(True)
        else:
            QMessageBox.warning(self, "错误", "请选择有效的 'git.exe' 文件。")
            self.git_status_label.setText("状态: [未锁定] 请手动选择 'git.exe'。")
            self.git_status_label.setStyleSheet("color: red;")
            self.clone_button.setEnabled(False)
            
    def clone_comfyui(self):
        if not self.main_window.git_exe_path or not os.path.exists(self.main_window.git_exe_path):
            QMessageBox.critical(self, "Git 错误", "Git 可执行文件路径无效，请检查 本地Git 设置。")
            return
            
        manual_target = self.clone_target_lineedit.text().strip()
        
        if manual_target:
            target_dir = manual_target
            if not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir)
                except Exception as e:
                    QMessageBox.critical(self, "目标目录错误", f"无法创建手动指定的目录: {target_dir}\n错误: {e}")
                    return
        elif self.main_window.project_dir and os.path.isdir(self.main_window.project_dir):
            target_dir = self.main_window.project_dir
        else:
            QMessageBox.critical(self, "目标路径错误", "请在上方手动指定克隆目录，或在 Tab 2 设置有效路径。")
            return

        if os.listdir(target_dir):
            reply = QMessageBox.question(self, '警告',
                f"目标目录 '{target_dir}' 不为空，继续克隆可能会导致文件冲突或覆盖。\n是否确定继续？", 
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.git_log_display.append("\n--- [用户取消] ---")
                return

        self.git_log_display.clear()
        self.git_log_display.append(f"--- [Git Clone] 正在克隆到: {target_dir} ---")
        self.clone_button.setEnabled(False)
        self.git_browse_btn.setEnabled(False)
        self.git_status_label.setText("状态: 正在执行 Git Clone...")
        self.git_status_label.setStyleSheet("color: blue;")
        
        self.git_process.setWorkingDirectory(target_dir)
        
        command = self.main_window.git_exe_path
        args = ['clone', 'https://github.com/comfyanonymous/ComfyUI.git', '.']
        
        self.git_log_display.append(f"[执行命令] {command} {' '.join(args)}")
        
        self.git_process.start(command, args)

    def handle_git_stdout(self):
        data = self.git_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.git_log_display.moveCursor(QTextCursor.End)
        self.git_log_display.insertPlainText(data)
        
    def handle_git_stderr(self):
        data = self.git_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.git_log_display.moveCursor(QTextCursor.End)
        self.git_log_display.insertPlainText(data)

    def handle_git_finished(self, exitCode, exitStatus):
        if exitStatus == QProcess.CrashExit or exitCode != 0:
            self.git_log_display.append(f"\n--- [失败] Git Clone 失败！退出代码: {exitCode} ---")
            self.git_status_label.setText("状态: Git Clone 失败。请检查日志。")
            self.git_status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Git Clone 失败", "Git Clone 操作未成功，请检查网络和日志。")
        else:
            self.git_log_display.append("\n--- [成功] Git Clone 完成 ---")
            self.git_status_label.setText("状态: ComfyUI 仓库克隆成功。")
            self.git_status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "成功", "ComfyUI 仓库已成功克隆！")

        self.clone_button.setEnabled(True)
        self.git_browse_btn.setEnabled(True)
        
    def apply_git_proxy(self):
        """应用 Git 代理设置"""
        if not self.main_window.git_exe_path or not os.path.exists(self.main_window.git_exe_path):
            QMessageBox.warning(self, "Git 错误", "请先设置有效的 Git 可执行文件路径。")
            return
            
        if not self.proxy_enabled_checkbox.isChecked():
            QMessageBox.information(self, "提示", "请先启用 Git 代理。")
            return
            
        # 检查输入
        http_addr = self.http_proxy_addr.text().strip()
        http_port = self.http_proxy_port.text().strip()
        https_addr = self.https_proxy_addr.text().strip()
        https_port = self.https_proxy_port.text().strip()
        
        if not http_addr or not http_port:
            QMessageBox.warning(self, "输入错误", "请填写完整的 HTTP 代理地址和端口。")
            return
            
        if not https_addr or not https_port:
            QMessageBox.warning(self, "输入错误", "请填写完整的 HTTPS 代理地址和端口。")
            return
            
        # 验证端口格式
        try:
            http_port_num = int(http_port)
            https_port_num = int(https_port)
            if not (1 <= http_port_num <= 65535) or not (1 <= https_port_num <= 65535):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "输入错误", "端口号必须在 1-65535 范围内。")
            return
            
        # 生成代理命令
        http_proxy = f"{self.http_proxy_type.currentText()}://{http_addr}:{http_port}"
        https_proxy = f"{self.https_proxy_type.currentText()}://{https_addr}:{https_port}"
        
        # 应用代理设置
        try:
            # 设置 HTTP 代理
            http_cmd = [self.main_window.git_exe_path, 'config', '--global', 'http.proxy', http_proxy]
            subprocess.run(http_cmd, check=True, capture_output=True)
            
            # 设置 HTTPS 代理
            https_cmd = [self.main_window.git_exe_path, 'config', '--global', 'https.proxy', https_proxy]
            subprocess.run(https_cmd, check=True, capture_output=True)
            
            # 更新主窗口变量和配置
            self.main_window.git_proxy_enabled = True
            self.main_window.git_http_proxy = http_proxy
            self.main_window.git_https_proxy = https_proxy
            
            self.git_log_display.append(f"[代理设置] HTTP 代理已设置为: {http_proxy}")
            self.git_log_display.append(f"[代理设置] HTTPS 代理已设置为: {https_proxy}")
            
            QMessageBox.information(self, "成功", "Git 代理设置已应用。")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "错误", f"设置 Git 代理时出错:\n{e.stderr.decode()}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置 Git 代理时出错:\n{str(e)}")

    def unset_git_proxy(self):
        """取消 Git 代理设置"""
        if not self.main_window.git_exe_path or not os.path.exists(self.main_window.git_exe_path):
            QMessageBox.warning(self, "Git 错误", "请先设置有效的 Git 可执行文件路径。")
            return
            
        try:
            # 取消 HTTP 代理
            http_cmd = [self.main_window.git_exe_path, 'config', '--global', '--unset', 'http.proxy']
            subprocess.run(http_cmd, check=True, capture_output=True)
            
            # 取消 HTTPS 代理
            https_cmd = [self.main_window.git_exe_path, 'config', '--global', '--unset', 'https.proxy']
            subprocess.run(https_cmd, check=True, capture_output=True)
            
            # 更新主窗口变量和配置
            self.main_window.git_proxy_enabled = False
            self.main_window.git_http_proxy = ""
            self.main_window.git_https_proxy = ""
            
            self.git_log_display.append("[代理设置] 已取消所有 Git 代理设置")
            
            QMessageBox.information(self, "成功", "Git 代理设置已取消。")
        except subprocess.CalledProcessError:
            # 如果没有设置过代理，会返回错误，这里忽略
            self.main_window.git_proxy_enabled = False
            self.main_window.git_http_proxy = ""
            self.main_window.git_https_proxy = ""
            self.git_log_display.append("[代理设置] 已取消所有 Git 代理设置")
            QMessageBox.information(self, "成功", "Git 代理设置已取消。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"取消 Git 代理时出错:\n{str(e)}")

    def check_git_proxy(self):
        """查看当前 Git 代理设置"""
        if not self.main_window.git_exe_path or not os.path.exists(self.main_window.git_exe_path):
            QMessageBox.warning(self, "Git 错误", "请先设置有效的 Git 可执行文件路径。")
            return
            
        try:
            # 获取所有 Git 配置
            cmd = [self.main_window.git_exe_path, 'config', '--global', '--list']
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            config_lines = result.stdout.strip().split('\n')
            proxy_lines = [line for line in config_lines if 'proxy' in line]
            
            self.git_log_display.append("\n--- [当前 Git 代理设置] ---")
            if proxy_lines:
                for line in proxy_lines:
                    self.git_log_display.append(line)
            else:
                self.git_log_display.append("未设置 Git 代理")
            self.git_log_display.append("--- [结束] ---")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "错误", f"查看 Git 配置时出错:\n{e.stderr.decode()}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查看 Git 配置时出错:\n{str(e)}")
            
    def update_ui_from_config(self, git_proxy_config):
        """从配置更新 UI"""
        try:
            self.proxy_enabled_checkbox.setChecked(git_proxy_config.getboolean('Enabled', False))
            http_proxy = git_proxy_config.get('HttpProxy', '')
            https_proxy = git_proxy_config.get('HttpsProxy', '')
            
            # 解析 HTTP 代理设置
            if http_proxy:
                if '://' in http_proxy:
                    protocol, addr_port = http_proxy.split('://', 1)
                    if ':' in addr_port:
                        addr, port = addr_port.rsplit(':', 1)
                        self.http_proxy_type.setCurrentText(protocol)
                        self.http_proxy_addr.setText(addr)
                        self.http_proxy_port.setText(port)
            
            # 解析 HTTPS 代理设置
            if https_proxy:
                if '://' in https_proxy:
                    protocol, addr_port = https_proxy.split('://', 1)
                    if ':' in addr_port:
                        addr, port = addr_port.rsplit(':', 1)
                        self.https_proxy_type.setCurrentText(protocol)
                        self.https_proxy_addr.setText(addr)
                        self.https_proxy_port.setText(port)
        except Exception as e:
            print(f"Error updating Git proxy UI from config: {e}")