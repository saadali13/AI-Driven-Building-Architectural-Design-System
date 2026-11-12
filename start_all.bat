@echo off
REM ============================================================================
REM ArchiCraft AI Studio - Production Startup Script
REM Starts Python Backend on Port 8000 and Vite React Frontend on Port 5173
REM ============================================================================

echo ============================================================================
echo Starting ArchiCraft AI Studio Services...
echo ============================================================================

cd /d "%~dp0"

echo [1/3] Checking Python dependencies...
python -c "import shapely, matplotlib, ezdxf; print('Python CAD libraries verified.')"
if %errorlevel% neq 0 (
    echo [ERROR] Required Python packages missing. Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [2/3] Starting Backend API Server (Port 8000)...
start "ArchiCraft API Server (Port 8000)" cmd /k "python api_server.py --port 8000"

echo [3/3] Starting Frontend Dev Server (Port 5173)...
cd /d "%~dp0frontend"
start "ArchiCraft Vite Frontend (Port 5173)" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173"

echo ============================================================================
echo Both servers have been launched!
echo Backend API : http://127.0.0.1:8000
echo Frontend UI : http://127.0.0.1:5173
echo ============================================================================

