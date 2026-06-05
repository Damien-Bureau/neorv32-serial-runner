:: Format terminal
@echo off
title NEORV32 Serial Runner - Setup
cls

:: FORCE UTF-8 ENCODING
chcp 65001 >nul

:: Force Windows to get the real ESC character for ANSI colors
for /f %%e in ('powershell -Command "[char]27"') do set "ESC=%%e"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "RESET=%ESC%[0m"
set "BOLD=%ESC%[1m"

echo %CYAN%╔═══════════════════════════════════════════════╗%RESET%
echo %CYAN%║  NEORV32 Serial Runner - Installation Wizard  ║%RESET%
echo %CYAN%╚═══════════════════════════════════════════════╝%RESET%
echo.

:: Check Python installation
<nul set /p ="Checking for Python installation..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%KO%RESET%
    echo %RED%Python is not installed or not added to PATH.%RESET%
    echo Please install Python and try again.
    goto error
)
echo %GREEN%OK%RESET%

:: Create Python venv
<nul set /p ="Creating Python virtual environment (.venv)..."
if exist ".venv" (
    echo %YELLOW%ALREADY EXISTS%RESET%
    goto activate_venv
)

python -m venv .venv
if %errorlevel% neq 0 (
    echo %RED%KO%RESET%
    echo %RED%Failed to create virtual environment.%RESET%
    goto error
)
echo %GREEN%OK%RESET%

:activate_venv
:: Activate venv
<nul set /p ="Activating virtual environment..."
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo %GREEN%OK%RESET%
) else (
    echo %RED%KO%RESET%
    echo %RED%Activation script not found. Is the venv corrupted?%RESET%
    goto error
)

:: Install required Python packages
if not exist "requirements.txt" (
    echo %RED%'requirements.txt' not found! Cannot install packages.%RESET%
    goto error
)

:: Upgrade pip
python -m pip install --upgrade pip >nul 2>&1

:: Install packages
<nul set /p ="   Installing required Python packages (this may take a moment)..."
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo %RED%KO%RESET%
    echo %RED%Failed to install dependencies.%RESET%
    goto error
)
echo %GREEN%OK%RESET%

:: End of script (success)
echo.
echo %GREEN%Setup completed successfully!%RESET%
echo You can now run your project using %CYAN%run.bat%RESET%
echo.
pause
exit /b 0

:: End of script (error)
:error
echo.
:: On force un RESET de couleur ici pour éviter le terminal tout jaune/rouge permanent
echo %RESET%%RED%Setup failed. Please check the errors above.%RESET%
echo.
pause
exit /b 1