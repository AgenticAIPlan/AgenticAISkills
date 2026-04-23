@echo off
chcp 65001 >nul
echo ==========================================
echo 政策追踪系统自动更新脚本
echo 时间: %date% %time%
echo ==========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python
    pause
    exit /b 1
)

:: 安装依赖（如果未安装）
echo [1/3] 检查依赖...
pip install requests beautifulsoup4 lxml pyyaml -q

:: 运行自动更新脚本
echo [2/3] 执行数据采集...
python auto_update.py

:: 记录执行日志
echo [3/3] 记录日志...
echo [%date% %time%] 自动更新执行完成 >> logs\auto_update.log

echo.
echo ==========================================
echo 自动更新完成！
echo ==========================================
