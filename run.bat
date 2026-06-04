:: Format terminal
@echo off
title NEORV32 Serial Runner
cls

:: Activate Python virtual environment
call .venv_windows\Scripts\activate.bat

:: Launch program
python main.py --show-logs --save-logs
