@echo off
echo ==========================================
echo UNIVERSAL WEB SCRAPER INSTALLER
echo ==========================================
echo.

py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Package installation failed.
    pause
    exit /b 1
)

echo.
echo Installing Chromium for JavaScript websites...
py -m playwright install chromium
if errorlevel 1 (
    echo.
    echo Chromium installation failed.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo INSTALLATION COMPLETE
echo ==========================================
echo.
pause
