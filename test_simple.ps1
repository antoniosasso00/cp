# Test API Nesting v1.4.12-DEMO
Write-Host "TEST API NESTING v1.4.12-DEMO" -ForegroundColor Green

# Test connessione server
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    Write-Host "Server raggiungibile" -ForegroundColor Green
} catch {
    Write-Host "Server non raggiungibile. Assicurati che sia avviato:" -ForegroundColor Red
    Write-Host "cd backend && uvicorn main:app --reload" -ForegroundColor Yellow
    exit 1
}

# Test 1: Algoritmo Standard
Write-Host "`nTEST 1: Algoritmo Standard" -ForegroundColor Cyan

$body1 = @{
    autoclave_id = 4
    allow_heuristic = $false
} | ConvertTo-Json

try {
    $result1 = Invoke-RestMethod -Uri "http://localhost:8000/batch_nesting/solve" -Method POST -Body $body1 -ContentType "application/json" -TimeoutSec 120
    
    $metrics1 = $result1.metrics
    Write-Host "Test 1 completato" -ForegroundColor Green
    Write-Host "Area: $([math]::Round($metrics1.area_utilization_pct, 1))%" -ForegroundColor White
    Write-Host "Vacuum: $([math]::Round($metrics1.vacuum_util_pct, 1))%" -ForegroundColor White
    Write-Host "Efficiency: $([math]::Round($metrics1.efficiency_score, 1))%" -ForegroundColor White
    Write-Host "Tempo: $([math]::Round($metrics1.time_solver_ms, 0))ms" -ForegroundColor White
    Write-Host "Fallback: $(if($metrics1.fallback_used) {'Si'} else {'No'})" -ForegroundColor White
    
} catch {
    Write-Host "Test 1 fallito: $($_.Exception.Message)" -ForegroundColor Red
    $result1 = $null
}

# Test 2: Algoritmo con Euristica
Write-Host "`nTEST 2: Algoritmo con Euristica RRGH" -ForegroundColor Cyan

$body2 = @{
    autoclave_id = 4
    allow_heuristic = $true
} | ConvertTo-Json

try {
    $result2 = Invoke-RestMethod -Uri "http://localhost:8000/batch_nesting/solve" -Method POST -Body $body2 -ContentType "application/json" -TimeoutSec 120
    
    $metrics2 = $result2.metrics
    Write-Host "Test 2 completato" -ForegroundColor Green
    Write-Host "Area: $([math]::Round($metrics2.area_utilization_pct, 1))%" -ForegroundColor White
    Write-Host "Vacuum: $([math]::Round($metrics2.vacuum_util_pct, 1))%" -ForegroundColor White  
    Write-Host "Efficiency: $([math]::Round($metrics2.efficiency_score, 1))%" -ForegroundColor White
    Write-Host "Tempo: $([math]::Round($metrics2.time_solver_ms, 0))ms" -ForegroundColor White
    Write-Host "Fallback: $(if($metrics2.fallback_used) {'Si'} else {'No'})" -ForegroundColor White
    Write-Host "Iterazioni RRGH: $($metrics2.heuristic_iters)" -ForegroundColor White
    
} catch {
    Write-Host "Test 2 fallito: $($_.Exception.Message)" -ForegroundColor Red
    $result2 = $null
}

# Confronto risultati
Write-Host "`nCONFRONTO RISULTATI" -ForegroundColor Yellow

if ($result1 -and $result2) {
    $eff1 = $result1.metrics.efficiency_score
    $eff2 = $result2.metrics.efficiency_score
    
    Write-Host "Standard: $([math]::Round($eff1, 1))%" -ForegroundColor White
    Write-Host "RRGH: $([math]::Round($eff2, 1))%" -ForegroundColor White
    Write-Host "Miglioramento: $([math]::Round($eff2 - $eff1, 1))%" -ForegroundColor $(if($eff2 > $eff1) {'Green'} else {'Red'})
    
    # Verifica target
    Write-Host "`nVERIFICA TARGET v1.4.12-DEMO" -ForegroundColor Yellow
    
    $best_area = [math]::Max($result1.metrics.area_utilization_pct, $result2.metrics.area_utilization_pct)
    $best_eff = [math]::Max($eff1, $eff2)
    
    Write-Host "Area migliore: $([math]::Round($best_area, 1))% (target >=75%)" -ForegroundColor White
    Write-Host "Efficiency migliore: $([math]::Round($best_eff, 1))% (target >=70%)" -ForegroundColor White
    
    $area_ok = $best_area -ge 75
    $eff_ok = $best_eff -ge 70
    
    Write-Host "Area target: $(if($area_ok) {'RAGGIUNTO'} else {'NON RAGGIUNTO'})" -ForegroundColor $(if($area_ok) {'Green'} else {'Red'})
    Write-Host "Efficiency target: $(if($eff_ok) {'RAGGIUNTO'} else {'NON RAGGIUNTO'})" -ForegroundColor $(if($eff_ok) {'Green'} else {'Red'})
    
    if ($area_ok -and $eff_ok) {
        Write-Host "`nTUTTI I TARGET RAGGIUNTI! Algoritmo v1.4.12-DEMO funziona!" -ForegroundColor Green
    } else {
        Write-Host "`nAlcuni target non raggiunti" -ForegroundColor Yellow
    }
} else {
    Write-Host "Impossibile confrontare - uno o entrambi i test sono falliti" -ForegroundColor Red
}

Write-Host "`nTest completato" -ForegroundColor Green 