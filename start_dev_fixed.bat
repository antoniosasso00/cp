@echo off
chcp 65001 >nul
echo ===============================
echo 🔵 Avvio CarbonPilot (Versione Corretta)
echo ===============================

rem Controlla se il backend è già in esecuzione
echo 🔍 Controllo se il backend è già attivo...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend già in esecuzione su http://localhost:8000
) else (
    echo 🚀 Avvio backend (FastAPI - Uvicorn)
    cd backend
    call ..\.venv\Scripts\activate.bat
    start "CarbonPilot Backend" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    cd ..
    
    rem Aspetta che il backend si avvii
    echo ⏳ Attendo che il backend si avvii...
    timeout /t 5 /nobreak >nul
    
    rem Verifica che il backend sia attivo
    :check_backend
    curl -s http://localhost:8000/health >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⏳ Backend ancora in avvio...
        timeout /t 2 /nobreak >nul
        goto check_backend
    )
    echo ✅ Backend avviato con successo!
)

rem Controlla se il frontend è già in esecuzione
echo 🔍 Controllo se il frontend è già attivo...
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend già in esecuzione su http://localhost:3000
) else (
    echo 🚀 Avvio frontend (Next.js)
    cd frontend
    start "CarbonPilot Frontend" cmd /k "npm run dev"
    cd ..
    
    echo ⏳ Attendo che il frontend si avvii...
    timeout /t 10 /nobreak >nul
)

echo.
echo ===============================
echo ✅ CarbonPilot avviato!
echo ===============================
echo 🔗 Backend:  http://localhost:8000
echo 🔗 Frontend: http://localhost:3000
echo 📚 API Docs: http://localhost:8000/docs
echo ===============================
echo.
echo Premi un tasto per aprire l'applicazione nel browser...
pause >nul

start http://localhost:3000

echo.
echo Premi un tasto per chiudere questo script...
pause 