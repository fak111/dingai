@echo off
REM DouyinLiveRecorder Windows 打包脚本
REM 用法: build.bat

setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ============================================
echo   DouyinLiveRecorder 打包脚本 (Windows)
echo ============================================
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] 未找到虚拟环境，请先创建虚拟环境: python -m venv venv
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
echo [INFO] 检查依赖...
pip install -q -r requirements.txt

REM 检查 ffmpeg
if not exist "bin\ffmpeg.exe" (
    echo [WARNING] 未找到 bin\ffmpeg.exe，请确保 ffmpeg 已放置在 bin/ 目录
)

REM 清理之前的构建
echo [INFO] 清理之前的构建...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM 开始打包
echo [INFO] 开始打包 (这可能需要几分钟)...
pyinstaller gui.spec --noconfirm

REM 验证打包结果
if exist "dist\DouyinLiveRecorder.exe" (
    echo.
    echo ============================================
    echo   打包成功！
    echo ============================================
    echo.
    echo [INFO] 输出目录: dist\DouyinLiveRecorder.exe
    echo.
    echo 使用方法:
    echo   1. 进入 dist 目录
    echo   2. 运行 DouyinLiveRecorder.exe
    echo.
    echo 注意:
    echo   - 确保 bin\ffmpeg.exe 存在，否则录制功能可能无法正常工作
    echo   - 首次运行可能需要较长时间启动
) else (
    echo [ERROR] 打包失败，请检查错误信息
    exit /b 1
)

echo.
echo [DONE] 打包完成！
endlocal
pause
