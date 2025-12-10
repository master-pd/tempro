@echo off
chcp 65001 >nul
cls

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║            🚀 TEMPRO BOT INSTALLER 🚀           ║
echo ║        Telegram Temporary Email Generator        ║
echo ║              Windows Installation                ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [✗] Python not found!
    echo.
    echo Please install Python 3.9 or higher:
    echo Download from: https://www.python.org/downloads/
    echo.
    echo During installation, make sure to:
    echo 1. Check "Add Python to PATH"
    echo 2. Install pip
    echo 3. Install for all users
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version') do set PYVER=%%i
echo [✓] Python %PYVER% detected

REM Check if Python 3.9+
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    if %%a LSS 3 (
        echo [✗] Python 3.9+ required!
        pause
        exit /b 1
    )
    if %%a EQU 3 (
        if %%b LSS 9 (
            echo [✗] Python 3.9+ required!
            pause
            exit /b 1
        )
    )
)

REM Check Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [✗] Git not found!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo.
    echo During installation, use default options.
    echo.
    pause
    exit /b 1
)
echo [✓] Git installed

REM Clone repository if needed
if not exist "setup_wizard.py" (
    echo [*] Cloning Tempro Bot repository...
    git clone https://github.com/master-pd/tempro.git tempro-bot
    cd tempro-bot
    echo [✓] Repository cloned
) else (
    echo [✓] Already in Tempro Bot directory
)

REM Create virtual environment
echo [*] Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [✗] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [*] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo [*] Installing requirements...
pip install -r requirements.txt

REM Create directories
echo [*] Creating directories...
mkdir data 2>nul
mkdir logs 2>nul
mkdir backups 2>nul
mkdir temp 2>nul
mkdir temp\cache 2>nul
mkdir config 2>nul

echo.
echo ══════════════════════════════════════════════════
echo 🎉 Tempro Bot installed successfully!
echo.
echo Next steps:
echo 1. Run the setup wizard:
echo    venv\Scripts\activate.bat
echo    python setup_wizard.py
echo.
echo 2. Start the bot:
echo    run.bat (will be created by setup wizard)
echo.
echo 3. For Docker installation:
echo    docker-compose up -d
echo.
echo ══════════════════════════════════════════════════
echo 📢 Channel: @tempro_updates
echo 👥 Support: @tempro_support
echo 💻 GitHub: github.com/master-pd/tempro
echo.

REM Ask to run setup wizard
set /p RUN_WIZARD="Run setup wizard now? (y/n): "
if /i "%RUN_WIZARD%"=="y" (
    echo [*] Starting setup wizard...
    python setup_wizard.py
)

pause