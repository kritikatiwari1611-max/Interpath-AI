# InternPath AI - Local & Cloud Setup Guide

## Local Quick Start (Windows, macOS, Linux)

### 1. Requirements
* Python 3.10 or higher installed on your computer.
* Git installed.

### 2. Windows 1-Click Launch
Double-click `start.bat` in the project root folder.
The script will automatically:
1. Create a Python virtual environment (`venv`).
2. Install all required dependencies (`pip install -r requirements.txt`).
3. Run `setup_wizard.py` to generate `.env`, initialize SQLite schema, and seed demo accounts.
4. Launch the application at `http://localhost:5000`.

### 3. macOS / Linux 1-Click Launch
Run the following terminal commands:
```bash
chmod +x start.sh
./start.sh
```

### 4. Manual Setup (Terminal)
```bash
# 1. Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run setup wizard
python scripts/setup_wizard.py

# 4. Start the server
python run.py
```
Open your browser to: `http://localhost:5000`

---

## Demo Accounts
* **Student (BCA - Tech Track):** `student@demo.com` / `Student@123`
* **Student (B.Com - Finance Track):** `priya@demo.com` / `Student@123`
* **Administrator:** `admin@demo.com` / `Admin@123`
