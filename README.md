# ComfyUI-Environment-Configuration-Tool
## Comfyui environment for AMD radeon and ROCm  
### Current AMD graphics card requirements: 7000 series and above
## to update! Nvidia GPU and CPU configuration is now supported (corresponding plugins need to be installed)  
### 专为懒狗和小白设计的部署工具，为了结合更多自定义效果没有做成一键部署的形式，但是足够靠谱  

**AMD Details:**   
https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html  
https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/  
https://www.amd.com/en/resources/support-articles/release-notes/RN-AMDGPU-WINDOWS-PYTORCH-PREVIEW.html  
### 已更新最新插件可用于cuda环境和cpu环境部署，有需要要的可以从plugins下载  
插件使用方法：从plugins下载或自己构建的py源码放在程序plugins文件夹中，自动识别在程序的addons选项卡中，勾选插件后点击加载按钮，如需卸载取消勾选后再次点击加载操作按钮  

    
AMD平台:  **1.** 从官网下载Hip SDK，选择rocm6.4及以上版本安装，rocm页面可以帮助你快速确认安装是否正确 **2.** 选择comfyui项目的目录，如果没有可以从git clone页面尝试下载 **3.** 虚拟环境中选择自动创建即可，下载完成后建议选择“手动选择venv目录”，选择comfyui_amd_venv目录，点击验证提示“venv 已确认”即成功 **4.** 在启动参数中选择你需要的参数，如果不需要就留默认 **5.** 点击启动即可  
N卡平台（插件）：  **1.** 检查自己cuda支持版本：打开命令提示符（cmd），输入nvidia-smi，第一行驱动版本号旁边的便是支持的cuda版本，例如【Driver Version: 566.36         CUDA Version: 12.7】则说明最高支持cuda12.7的环境，可以选择安装cuda12.6，cuda11.8等版本，但要安装12.8等更高版本需要更新cuda **2.** comfyui选择同amd平台 **3.** 虚拟环境配置页面选择自动创建后选择pytorch版本，选择官方源下载，开始创建，完成后操作同amd平台 **4.** rocm选项卡为不可用状态，不必理会 **5.** 启动同amd平台  
纯CPU环境（插件）：  **1.** 选择comfyui项目同A,N平台 **2.** 创建环境时不需要理会各个版本后的cuda版本，找合适的pytorch版本（例如PyTorch 2.8.0），并勾选cpu模式下载，完成后同A,N平台步骤 **3.** 在启动参数中自定义参数务必添加“--cpu”参数 
#### 安装环境完成后想确认环境版本可以在venv手动选择环境目录，在启动页面点击启动会自动运行一次【正在收集 Torch 环境信息】，此时可以查看PyTorch version，例如【2.7.1+cu126】即pytroch2.7.1+cuda 12.6  
#### 如果没有任何信息或仅显示pytorch信息就退出那么极有可能你没安装正确的平台，例如你使用nvidia显卡cuda环境却安装了amd的rocm版torch  
#### 作者蹩脚，业余，有问题欢迎交流：BiliBili：1999Pt
2025/10/27更新：**1.** 为适应comfyui插件等功能需求，更新了comfyui实例调用git的逻辑   **2.** 用户可以自主选择git的目录，程序也会自动检测系统中存在的git path   **3.** git_clone现在支持自由克隆项目和克隆目标，同时支持配置对应git代理
