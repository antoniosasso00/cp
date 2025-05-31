@echo off
chcp 65001 >nul
echo ===============================
echo 🔵 CarbonPilot Smart Starter
echo ===============================

rem Controlla se il backend è già in esecuzione
echo 🔍 Controllo stato backend (porta 8000)...
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend già attivo su porta 8000
    curl -s http://localhost:8000/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Backend risponde correttamente
        set BACKEND_OK=1
    ) else (
        echo ⚠️  Backend sulla porta 8000 ma non risponde
        echo 🔄 Terminazione processi sulla porta 8000...
        for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000') do taskkill /PID %%i /F >nul 2>&1
        set BACKEND_OK=0
    )
) else (
    echo 🚀 Nessun backend attivo
    set BACKEND_OK=0
)

rem Controlla se il frontend è già in esecuzione
echo 🔍 Controllo stato frontend (porta 3000)...
netstat -ano | findstr :3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend già attivo su porta 3000
    set FRONTEND_OK=1
) else (
    echo 🚀 Nessun frontend attivo
    set FRONTEND_OK=0
)

rem Avvia backend se necessario
if %BACKEND_OK%==0 (
    echo 🚀 Avvio backend...
    
    rem Prova diverse strategie per l'environment
    echo 🔍 Tentativo 1: Ambiente virtuale locale...
    if exist ".venv\Scripts\python.exe" (
        cd backend
        start "CarbonPilot Backend" cmd /k "..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        cd ..
    ) else (
        echo ⚠️  .venv non trovato, uso Python di sistema...
        cd backend
        start "CarbonPilot Backend" cmd /k "python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        cd ..
    )
    
    echo ⏳ Attendo avvio backend (10 secondi)...
    timeout /t 10 /nobreak >nul
    
    rem Verifica che il backend sia attivo
    curl -s http://localhost:8000/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Backend avviato con successo!
    ) else (
        echo ❌ Errore nell'avvio backend
        echo 💡 Prova manualmente: cd backend && python -m uvicorn main:app --reload --port 8000
    )
)

rem Avvia frontend se necessario
if %FRONTEND_OK%==0 (
    echo 🚀 Avvio frontend...
    cd frontend
    start "CarbonPilot Frontend" cmd /k "npm run dev"
    cd ..
    
    echo ⏳ Attendo avvio frontend (15 secondi)...
    timeout /t 15 /nobreak >nul
)

echo.
echo ===============================
echo ✅ CarbonPilot Status Check
echo ===============================
echo 🔗 Backend:  http://localhost:8000
echo 🔗 Frontend: http://localhost:3000
echo 📚 API Docs: http://localhost:8000/docs
echo 🎯 Nesting:  http://localhost:3000/dashboard/curing/nesting/auto-multi
echo ===============================

rem Test finale
echo 🧪 Test finale connettività...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend OK
) else (
    echo ❌ Backend non raggiungibile
)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend OK
) else (
    echo ❌ Frontend non raggiungibile
)

echo.
echo 🚀 Apertura applicazione nel browser...
start http://localhost:3000/dashboard/curing/nesting/auto-multi

echo.
echo Premi un tasto per chiudere questo script...
pause 