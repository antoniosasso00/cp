@echo off
echo 🚀 AVVIO CARBON PILOT - Sistema Completo
echo ========================================

echo.
echo 📡 1. Avvio Backend (Porta 8000)...
echo --------------------------------
cd backend
start "CarbonPilot Backend" cmd /k "python main.py"
timeout /t 3 /nobreak >nul

echo.
echo 🌐 2. Avvio Frontend (Porta 3000)...
echo ---------------------------------
cd ..\frontend
start "CarbonPilot Frontend" cmd /k "npm run dev"

echo.
echo ⏳ Attesa avvio servizi...
timeout /t 5 /nobreak >nul

echo.
echo 🔍 3. Test Connessioni...
echo ------------------------
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Backend: OK (http://localhost:8000)
) else (
    echo ❌ Backend: Non raggiungibile
)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Frontend: OK (http://localhost:3000)
) else (
    echo ⚠️ Frontend: In avvio... (attendere)
)

echo.
echo 🎯 CARBON PILOT AVVIATO!
echo ========================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Docs API: http://localhost:8000/docs
echo.
echo Premi un tasto per aprire il browser...
pause >nul

start http://localhost:3000

echo.
echo ✅ Sistema avviato con successo!
echo Per fermare i servizi, chiudere le finestre del terminale.
pause 