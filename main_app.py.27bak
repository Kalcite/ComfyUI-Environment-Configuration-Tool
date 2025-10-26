# main_app.py
import sys
import os
import configparser
# import datetime
# import atexit
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PyQt5.QtCore import QProcess, QDir, Qt
from PyQt5.QtGui import QTextCursor, QIcon

# #全局日志记录器
# TEMP_LOG_FILE = 'comfy_launcher.log.temp'
# classStream = None # 设置全局以保持文件句柄打开

# class Logger:
#     def __init__(self, filename):
#         self.terminal = sys.stdout
#         # 将日志文件放在程序根目录
#         self.log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        
#         global classStream
#         try:
#             # 'w' 模式：每次启动都覆盖旧的临时日志
#             classStream = open(self.log_path, 'w', encoding='utf-8', errors='ignore')
#             self.log = classStream
#             print(f"--- [Logger] 临时日志已开启: {self.log_path} ---")
#         except Exception as e:
#             print(f"致命错误: 无法打开日志文件 {self.log_path}: {e}")
#             self.log = None
        
#         # 注册退出时要调用的函数
#         atexit.register(self.cleanup_and_rename)

#     def write(self, message):
#         try:
#             self.terminal.write(message) # 1. 写入原始控制台
#             if self.log:
#                 self.log.write(message) # 2. 写入日志文件
#                 self.log.flush()        # 确保立即写入
#         except Exception:
#             pass # 避免在日志记录时崩溃

#     def flush(self):
#         self.terminal.flush()
#         if self.log:
#             self.log.flush()
    
#     def cleanup_and_rename(self):

#         global classStream
#         end_time = datetime.datetime.now()
#         end_time_str = end_time.strftime("%Y_%m_%d_%H_%M_%S")
        
#         print(f"--- [Logger] 应用在 {end_time_str} 退出 ---")
        
#         if self.log:
#             print(f"Logger: 正在关闭临时日志 {self.log_path}")
#             self.log.close()
#             classStream = None
            
#             # 构造新的文件名
#             new_log_name = f"{end_time_str}.log"
#             new_log_path = os.path.join(os.path.dirname(self.log_path), new_log_name)
            
#             try:
#                 os.rename(self.log_path, new_log_path)
#                 self.terminal.write(f"Logger: 日志已保存为 {new_log_path}\n")
#             except Exception as e:
#                 self.terminal.write(f"Logger: 无法重命名日志文件: {e}\n")

# 导入所有Tab类
from ui.tab_system_info import TabSystemInfo
from ui.tab_project_path import TabProjectPath
from ui.tab_venv import TabVenv
from ui.tab_rocm_check import TabRocmCheck
from ui.tab_launch_options import TabLaunchOptions
from ui.tab_launch import TabLaunch
from ui.tab_git_clone import TabGitClone
from ui.tab_addons import TabAddons

# 全局常量(供 Tab 3 等模块导入)
CONFIG_FILE = 'config.ini'
Tsinghua_Mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"

AMD_TORCH_WHEELS = [
    "https://repo.radeon.com/rocm/windows/rocm-rel-6.4.4/torch-2.8.0a0%2Bgitfc14c65-cp312-cp312-win_amd64.whl",
    "https://repo.radeon.com/rocm/windows/rocm-rel-6.4.4/torchaudio-2.6.0a0%2B1a8f621-cp312-cp312-win_amd64.whl",
    "https://repo.radeon.com/rocm/windows/rocm-rel-6.4.4/torchvision-0.24.0a0%2Bc85f008-cp312-cp312-win_amd64.whl"
]

class ComfyUI_AMD_Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComfyUI (支持AMD ROCm) 快速配置工具")
        self.setGeometry(100, 100, 1100, 900)
        self.setWindowIcon(QIcon("./icon.ico"))

        # 共享状态变量
        self.project_dir = ""
        self.venv_dir = ""
        self.venv_dir_nv = "" # 预留更新插件使用
        self.python_interpreters = {} # 'path': 'version'
        self.git_exe_path = ""
        
        # 共享配置
        self.config = configparser.ConfigParser()
        self.load_config()

        # 初始化状态栏 (供插件使用)
        self.statusBar().showMessage("准备就绪。")

        self.initUI()
        
        # 启动时自动刷新 Tab 1 (它会自动触发 Tab 3 的更新)
        self.tab1.refresh_tab1_info() 
        
        # 从配置初始化UI
        self.update_ui_from_config()

    def initUI(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 组装 Tabs
        # 实例化每个 Tab，并将主窗口(self)的引用传递给它们
        self.tab1 = TabSystemInfo(self)
        self.tab2 = TabProjectPath(self)
        self.tab3 = TabVenv(self)
        self.tab4 = TabRocmCheck(self)
        self.tab5 = TabLaunchOptions(self)
        self.tab6 = TabLaunch(self)
        self.tab7 = TabGitClone(self)
        self.tab8 = TabAddons(self)

        # 按顺序添加 Tabs
        self.tabs.addTab(self.tab1, "1 系统检测")
        self.tabs.addTab(self.tab2, "2 项目路径")
        self.tabs.addTab(self.tab3, "3 虚拟环境")
        self.tabs.addTab(self.tab4, "4 ROCm 检测")
        self.tabs.addTab(self.tab5, "5 启动选项")
        self.tabs.addTab(self.tab6, "6 启动")
        self.tabs.addTab(self.tab7, "7 Git Clone")
        self.tabs.addTab(self.tab8, "8 Addons")


    # 共享的配置
    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        
        try:
            self.config.read(CONFIG_FILE)
            if 'Paths' in self.config:
                self.project_dir = self.config['Paths'].get('ProjectDir', '')
                self.venv_dir = self.config['Paths'].get('VenvDir', '')
                self.venv_dir_nv = self.config['Paths'].get('VenvDir_NV', '') # 预留新插件使用
        except Exception as e:
            print(f"Error loading config: {e}")
        
    def save_config(self):
        try:
            if 'Paths' not in self.config:
                self.config['Paths'] = {}
            if self.project_dir:
                self.config['Paths']['ProjectDir'] = self.project_dir
            if self.venv_dir:
                self.config['Paths']['VenvDir'] = self.venv_dir
            if hasattr(self, 'venv_dir_nv') and self.venv_dir_nv:
                self.config['Paths']['VenvDir_NV'] = self.venv_dir_nv # 预留新插件使用

            if 'LaunchArgs' not in self.config:
                self.config['LaunchArgs'] = {}
            # 从 Tab 5 获取数据
            self.config['LaunchArgs']['Listen'] = self.tab5.get_listen_addr()
            self.config['LaunchArgs']['Port'] = self.tab5.get_port()
            self.config['LaunchArgs']['Other'] = self.tab5.get_other_args()

            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"Error saving config: {e}") 
            
            

    def update_ui_from_config(self):
        """在启动时，将加载的配置分发到各个 Tab"""
        try:
            self.tab2.update_ui_from_config(self.project_dir)
            self.tab3.update_ui_from_config(self.venv_dir)
            
            if 'LaunchArgs' in self.config:
                self.tab5.update_ui_from_config(self.config['LaunchArgs'])
        except Exception as e:
            print(f"Error updating UI from config: {e}")

    def closeEvent(self, event):
        self.save_config()
        
        # 退出时尝试终止所有子进程
        try:
            if self.tab3.install_process.state() == QProcess.ProcessState.Running:
                self.tab3.install_process.terminate()
            if self.tab6.launch_process.state() == QProcess.ProcessState.Running:
                self.tab6.launch_process.terminate()
            if self.tab7.git_process.state() == QProcess.ProcessState.Running:
                self.tab7.git_process.terminate()
        except Exception as e:
            print(f"Error terminating processes on close: {e}")
            
        super().closeEvent(event)


def ensure_dir_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

if __name__ == "__main__":
    # 确保 ui 和 plugins 目录存在
    ensure_dir_exists("ui")
    ensure_dir_exists("plugins")
    
    app = QApplication(sys.argv)
    window = ComfyUI_AMD_Launcher()
    window.show()

    sys.exit(app.exec_())
