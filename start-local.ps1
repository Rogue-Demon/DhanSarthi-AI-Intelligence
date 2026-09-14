# DhanSarthi Local Development Startup Script
Write-Host "==========================================================" -ForegroundColor Cyans
Write-Host "  Starting DhanSarthi Local Financial Intelligence App   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyans

$BackendVenv = "d:\DhanSarthi\backend\.venv\Scripts\python.exe"
$BackendDir  = "d:\DhanSarthi\backend"
$FrontendDir = "d:\DhanSarthi\frontend"

Write-Host "`n1. Verifying Local PostgreSQL Database connection..." -ForegroundColor Yellow
& $BackendVenv -c "
import psycopg
try:
    with psycopg.connect('postgresql://postgres:shreyanshu0805@127.0.0.1:5432/dhansarthi') as conn:
        print('   ✓ Local PostgreSQL [dhansarthi] connected successfully!')
except Exception as e:
    print('   ❌ Could not connect to local PostgreSQL: ', e)
"

Write-Host "`n2. Starting Local FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process -FilePath $BackendVenv -ArgumentList "-m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -WorkingDirectory $BackendDir

Write-Host "`n3. Starting Local Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory $FrontendDir

Write-Host "`n✓ Both Backend and Frontend services launched in background!" -ForegroundColor Green
Write-Host "  - Frontend UI: http://localhost:5173" -ForegroundColor White
Write-Host "  - Backend API: http://127.0.0.1:8000/api/v1" -ForegroundColor White
Write-Host "  - PostgreSQL DB: 127.0.0.1:5432/dhansarthi" -ForegroundColor White
