@echo off
TITLE InternPath AI Runner
echo Starting InternPath AI Environment...

IF NOT EXIST "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating environment and installing dependencies...
call venv\Scripts\activate
python -m pip install -r requirements.txt

echo Running setup checks...
python scripts\setup_wizard.py

echo Starting Flask Application Server...
python run.py

pause
