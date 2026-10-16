#!/usr/bin/env bash
set -e

echo "Starting InternPath AI Environment..."

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

python scripts/setup_wizard.py
python run.py
