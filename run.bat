:: Format terminal
@echo off
title NEORV32 Serial Runner - Launcher
cls

:: Force UTF-8 encoding
chcp 65001 >nul

:: Force Windows to get the real ESC character for ANSI colors
for /f %%e in ('powershell -Command "[char]27"') do set "ESC=%%e"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "RESET=%ESC%[0m"

:: Initialize argument variables
set "ARGS="

:: If arguments were passed directly in the command line (e.g., from a terminal),
:: skip the interactive questions and launch immediately!
if not "%*"=="" (
    set "ARGS=%*"
    goto launch
)

echo %CYAN%╔═══════════════════════════════════════════════╗%RESET%
echo %CYAN%║        NEORV32 Serial Runner - Launch         ║%RESET%
echo %CYAN%╚═══════════════════════════════════════════════╝%RESET%
echo.

:: Check that Python virtual environment exists
<nul set /p "=Checking Python virtual environment..."
if not exist ".venv\Scripts\activate.bat" (
    echo %RED%KO%RESET%
    echo.
    echo %YELLOW%Please run setup.bat first to install the required packages.%RESET%
    echo.
    pause
    exit /b
)
echo %GREEN%OK%RESET%

:: First arg: Show Logs
:question_show
set "CHOICE_SHOW=N"
set /p "CHOICE_SHOW=Display serial output in terminal? (y/N) : "
if /i "%CHOICE_SHOW%"=="Y" (
    set "ARGS=%ARGS% --show-logs"
    goto question_save
)
if /i "%CHOICE_SHOW%"=="N" goto question_save
echo %RED%Invalid choice, please enter Y or N.%RESET%
goto question_show

:: Second arg: Save Logs
:question_save
:question_save_loop
set "CHOICE_SAVE=N"
set /p "CHOICE_SAVE=Save serial output into a log file? (y/N) : "
if /i "%CHOICE_SAVE%"=="Y" (
    set "ARGS=%ARGS% --save-logs"
    goto question_bin
)
if /i "%CHOICE_SAVE%"=="N" goto question_bin
echo %RED%Invalid choice, please enter Y or N.%RESET%
goto question_save_loop

:: Third arg: Pick Binary File
:question_bin
set "CHOICE_BIN=N"
set /p "CHOICE_BIN=Select binary file using File Explorer? (y/N) : "
if /i "%CHOICE_BIN%"=="Y" (
    set "ARGS=%ARGS% --bin"
    goto launch
)
if /i "%CHOICE_BIN%"=="N" goto launch
echo %RED%Invalid choice, please enter Y or N.%RESET%
goto question_bin

:launch
echo.
echo Starting application with options:%ARGS%
echo.

:: Activate Python virtual environment
call .venv\Scripts\activate.bat

:: Launch program with the configured or forwarded arguments
python main.py %ARGS%

echo.
pause
