# Setting Up Python Interpreter for VS Code / Cursor

## Current Issue
You're currently using the **system Python interpreter** (`C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe`), which may not have all your packages installed, or Pyright can't detect them properly.

## Solution: Select the Correct Python Interpreter

### Step 1: Check if you have a virtual environment

**For OFH-Dashboard/backend:**
- Check if there's a `.venv` or `venv` folder in `OFH-Dashboard/backend/`
- If not, create one:
  ```powershell
  cd "C:\NINA Guardrail-Monitor\OFH-Dashboard\backend"
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

**For Guardrail-Strategy:**
- There's already a `venv` folder at `Guardrail-Strategy/venv`

### Step 2: Select the Interpreter in VS Code/Cursor

1. **Press `Ctrl+Shift+P`** (Command Palette)
2. Type: **"Python: Select Interpreter"**
3. Choose one of these options:

   **For OFH-Dashboard/backend files:**
   - `.\OFH-Dashboard\backend\.venv\Scripts\python.exe` (if you created it)
   - OR `.\OFH-Dashboard\backend\venv\Scripts\python.exe` (if it exists)

   **For Guardrail-Strategy files:**
   - `.\Guardrail-Strategy\venv\Scripts\python.exe`

### Step 3: Verify the Selection

1. Open a Python file (e.g., `base_service.py`)
2. Look at the bottom-right corner of VS Code/Cursor
3. You should see the Python version and path (e.g., `Python 3.11.9 ('venv': venv)`)
4. Click it to change if needed

### Step 4: Reload the Window (Restart Pyright)

After selecting the interpreter, reload Cursor to restart Pyright:
1. Press `Ctrl+Shift+P`
2. Type: **"Developer: Reload Window"** (or **"Reload Window"**)
3. This will reload Pyright with the correct interpreter

**Alternative:** Just close and reopen Cursor - Pyright will auto-reload.

## Alternative: Workspace-Specific Settings

If you want different interpreters for different folders, you can create a `.vscode/settings.json` file:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/OFH-Dashboard/backend/.venv/Scripts/python.exe"
}
```

## Why This Matters

- **Pyright** needs to know where your packages are installed
- If it can't find them, it reports "Import could not be resolved" errors
- Using the correct venv ensures Pyright can see all installed packages
- This eliminates false positives for missing imports

## Quick Check Command

Run this to see which Python you're using:
```powershell
python -c "import sys; print(sys.executable)"
```

If it shows a path like `C:\Users\...\AppData\Local\Programs\Python\...`, you're using system Python, not a venv.

