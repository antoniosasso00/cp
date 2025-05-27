@echo off
setlocal EnableDelayedExpansion

echo ================================================
echo      Script Git: Commit + Push + Tag (Windows)
echo ================================================

:: Messaggio di commit
set /p COMMIT_MSG=➡️  Inserisci il messaggio del commit: 

:: Nome del tag
set /p TAG_NAME=➡️  Inserisci il nome del tag (es. vX.X.X): 

:: Messaggio del tag
set /p TAG_MSG=➡️  Inserisci il messaggio del tag: 

echo.
echo 🌀 Eseguo: git add .
git add .

echo 🌀 Eseguo: git commit -m "!COMMIT_MSG!"
git commit -m "!COMMIT_MSG!"

echo 🌀 Eseguo: git push
git push

echo 🌀 Creo tag "!TAG_NAME!" con messaggio "!TAG_MSG!"
git tag -a !TAG_NAME! -m "!TAG_MSG!"

echo 🌀 Eseguo: git push origin !TAG_NAME!
git push origin !TAG_NAME!

echo.
echo ✅ Operazione completata con successo!
pause
