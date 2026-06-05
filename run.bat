:: Format terminal
@echo off
title NEORV32 Serial Runner
cls

:: Activate Python virtual environment
call .venv\Scripts\activate.bat

:: Launch program
python main.py %*

pause
