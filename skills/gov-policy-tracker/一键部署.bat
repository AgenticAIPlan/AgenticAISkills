@echo off
chcp 65001 >nul
title 政策追踪系统 - 一键部署
echo ==========================================
echo    政策追踪系统 - 定时任务部署
echo ==========================================
echo.
echo 即将创建每天上午10点自动更新的任务
echo.
pause

:: 以管理员身份运行PowerShell脚本
powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File ""%~dp0setup_scheduled_task.ps1""' -Verb RunAs -Wait"

echo.
echo ==========================================
echo 部署完成！
echo ==========================================
pause
