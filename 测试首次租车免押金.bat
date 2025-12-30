@echo off
chcp 65001 >nul
echo ======================================
echo   测试首次租车免押金功能
echo ======================================
echo.

cd /d "%~dp0code\car_rental_system"

echo 正在测试首次租车免押金功能...
echo.

python manage.py test_first_rental_deposit

echo.
echo ======================================
echo   测试完成！
echo ======================================
echo.
pause
