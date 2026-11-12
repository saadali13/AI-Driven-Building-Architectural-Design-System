# ============================================================================
# ArchiCraft AI Studio - Production Startup Script (PowerShell)
# Starts Python Backend on Port 8000 and Vite React Frontend on Port 5173
# ============================================================================

$ProjectRoot = $PSScriptRoot

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Starting ArchiCraft AI Studio Services..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

# 1. Dependency Check
Write-Host "[1/3] Verifying Python CAD dependencies..." -ForegroundColor Yellow
python -c "import shapely, matplotlib, ezdxf; print('Python CAD libraries verified.')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Missing Python CAD packages. Run: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

# 2. Launch Backend on Port 8000
Write-Host "[2/3] Launching Python Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python api_server.py --port 8000"

# 3. Launch Frontend on Port 5173
Write-Host "[3/3] Launching Vite Frontend on http://127.0.0.1:5173..." -ForegroundColor Green
$FrontendDir = Join-Path $ProjectRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FrontendDir'; npm run dev -- --host 127.0.0.1 --port 5173"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Both servers started successfully!" -ForegroundColor Cyan
Write-Host "Backend API : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Frontend UI : http://127.0.0.1:5173" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan

