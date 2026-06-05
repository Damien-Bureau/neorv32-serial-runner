:: Format terminal
@echo off
title NEORV32 Serial Runner - Launcher
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

:question_save
:: Second arg: Save Logs
:question_save_loop
set "CHOICE_SAVE=N"
set /p "CHOICE_SAVE=Save serial output into a log file? (y/N) : "
if /i "%CHOICE_SAVE%"=="Y" (
    set "ARGS=%ARGS% --save-logs"
    goto launch
)
if /i "%CHOICE_SAVE%"=="N" goto launch
echo %RED%Invalid choice, please enter Y or N.%RESET%
goto question_save_loop

:launch
echo.
echo %GREEN%Starting application with options:%RESET% %ARGS%
echo.

:: Activate Python virtual environment
call .venv\Scripts\activate.bat

:: Launch program with the configured or forwarded arguments
python main.py %ARGS%

echo.
echo %CYAN%Process finished.%RESET%
pause
