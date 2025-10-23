@echo off
pyinstaller --name="ComfyUI-AMD-Launcher" ^
            --windowed ^
            --icon="icon.ico" ^
            --add-data="plugins;plugins" ^
            --hidden-import=wmi ^
            --clean ^
            main_app.py
pause