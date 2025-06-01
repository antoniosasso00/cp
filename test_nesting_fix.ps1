# Test per verificare se il fix del proxy funziona
Write-Host "🔧 Test del fix del proxy per il nesting..." -ForegroundColor Cyan

# Test 1: Backend diretto
Write-Host "1. Test backend diretto..." -ForegroundColor Yellow
try {
    $backendResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/nesting/health" -Method GET -TimeoutSec 5
    Write-Host "✅ Backend OK: $($backendResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend ERRORE: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Frontend proxy
Write-Host "2. Test proxy frontend..." -ForegroundColor Yellow
try {
    $proxyResponse = Invoke-RestMethod -Uri "http://localhost:3000/api/v1/nesting/health" -Method GET -TimeoutSec 5
    Write-Host "✅ Proxy OK: $($proxyResponse.status)" -ForegroundColor Green
    Write-Host "🎉 FIX FUNZIONA! Il proxy ora instrada correttamente." -ForegroundColor Green
} catch {
    Write-Host "❌ Proxy ERRORE: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "⚠️ Il frontend potrebbe non essere ancora riavviato con le nuove configurazioni." -ForegroundColor Yellow
}

Write-Host "📋 Test completato." -ForegroundColor Cyan 