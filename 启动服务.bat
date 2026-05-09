@echo off
chcp 65001 >nul
echo ============================================
echo   Foodaily 内容生产系统 - 启动服务
echo ============================================
echo.
echo [1/2] 启动后端 API 服务器...
cd /d "%~dp0server"
start "Foodaily API Server" cmd /k python app.py
echo.
echo [2/2] 后端启动中，请等待3秒...
timeout /t 3 /nobreak >nul
echo.
echo ============================================
echo   服务已启动！
echo   后端API: http://localhost:5000
echo   前端页面: 请在浏览器打开 foodaily-system.html
echo ============================================
echo.
echo 提示：首次抓取需要1-2分钟，请耐心等待
echo.
pause
