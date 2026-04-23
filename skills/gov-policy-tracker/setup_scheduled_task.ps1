# 设置政策追踪自动更新定时任务
# 以管理员身份运行此脚本

$taskName = "政策追踪自动更新"
$taskDescription = "每天早上10点自动采集前一天的政策新闻数据"
$scriptPath = "C:\Users\renmeijing\ComateProjects\comate-zulu-demo\policy-tracker\run_auto_update.bat"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "政策追踪系统 - 定时任务设置" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否以管理员身份运行
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[错误] 请以管理员身份运行此脚本！" -ForegroundColor Red
    Write-Host "右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    pause
    exit 1
}

# 检查脚本文件是否存在
if (-not (Test-Path $scriptPath)) {
    Write-Host "[错误] 找不到脚本文件: $scriptPath" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[1/5] 检查现有任务..." -ForegroundColor Yellow
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "       发现现有任务，将先删除旧任务..." -ForegroundColor Cyan
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Write-Host "[2/5] 创建任务动作..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute $scriptPath

Write-Host "[3/5] 设置触发器（每天10:00）..." -ForegroundColor Yellow
$trigger = New-ScheduledTaskTrigger -Daily -At "10:00AM"

Write-Host "[4/5] 配置任务设置..." -ForegroundColor Yellow
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun

Write-Host "[5/5] 注册任务..." -ForegroundColor Yellow
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description $taskDescription `
    -RunLevel Highest

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "定时任务创建成功！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "任务详情:"
Write-Host "  - 任务名称: $taskName"
Write-Host "  - 执行时间: 每天早上 10:00"
Write-Host "  - 执行脚本: $scriptPath"
Write-Host ""
Write-Host "操作命令:"
Write-Host "  - 立即运行: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  - 查看状态: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "  - 删除任务: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
Write-Host ""

# 询问是否立即测试
$testNow = Read-Host "是否立即测试运行一次？(Y/N)"
if ($testNow -eq "Y" -or $testNow -eq "y") {
    Write-Host ""
    Write-Host "正在启动任务..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $taskName
    Write-Host "任务已启动！请查看飞书表格是否有更新。" -ForegroundColor Green
}

Write-Host ""
Write-Host "按任意键退出..."
pause
