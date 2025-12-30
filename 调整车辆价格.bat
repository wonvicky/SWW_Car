@echo off
chcp 65001 >nul
echo ======================================
echo   调整车辆租金和押金价格工具
echo ======================================
echo.

cd /d "%~dp0code\car_rental_system"

echo 正在调整车辆价格到合理水平...
echo.

python manage.py adjust_vehicle_pricing

echo.
echo ======================================
echo   调整完成！
echo ======================================
echo.
pause
