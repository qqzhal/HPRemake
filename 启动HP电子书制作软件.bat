@echo off
cd /d "%~dp0"

python -c "import customtkinter" >nul 2>nul
if errorlevel 1 (
    echo [HP Ebook] First run: installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [HP Ebook] Dependency install failed.
        pause
        exit /b 1
    )
)

for /f "delims=" %%P in ('python -c "import sys;print(sys.executable)"') do set "PYW=%%~dpPpythonw.exe"
if exist "%PYW%" (
    start "" "%PYW%" main.py
) else (
    start "" pythonw main.py
)
exit /b 0
