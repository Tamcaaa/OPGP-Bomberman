@echo off
cd /d %~dp0

REM Activate virtual environment
call .venv\Scripts\activate

REM Start two instances of the game
start cmd /k "python main.py"
start cmd /k "python main.py"

exit