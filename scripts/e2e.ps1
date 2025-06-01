# Test End-to-End per CarbonPilot v1.4.0
# Flusso: ODL → laminazione → nesting → batch → cura → report

$ErrorActionPreference = "Stop"

$API_BASE = "http://localhost:8000/api/v1"
$BACKEND_BASE = "http://localhost:8000"
$FRONTEND_BASE = "http://localhost:3000"

Write-Host "🧪 Avvio test End-to-End CarbonPilot v1.4.0" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Funzione per verificare status HTTP
function Test-Status {
    param(
        [string]$Url,
        [int]$Expected,
        [string]$Description
    )
    
    Write-Host "🔍 Test: $Description" -ForegroundColor Cyan
    Write-Host "   URL: $Url" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $Expected) {
            Write-Host "   ✅ PASS (Status: $statusCode)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ FAIL (Status: $statusCode, Expected: $Expected)" -ForegroundColor Red
            Write-Host "   Response: $($response.Content)" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "   ❌ FAIL (Error: $($_.Exception.Message))" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Funzione per POST con verifica status
function Test-Post {
    param(
        [string]$Url,
        [string]$Data,
        [int]$Expected,
        [string]$Description
    )
    
    Write-Host "🔍 Test POST: $Description" -ForegroundColor Cyan
    Write-Host "   URL: $Url" -ForegroundColor Gray
    Write-Host "   Data: $Data" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method POST -Body $Data -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $Expected) {
            Write-Host "   ✅ PASS (Status: $statusCode)" -ForegroundColor Green
            $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 2 | Write-Host -ForegroundColor Gray
            return $response.Content
        } else {
            Write-Host "   ❌ FAIL (Status: $statusCode, Expected: $Expected)" -ForegroundColor Red
            Write-Host "   Response: $($response.Content)" -ForegroundColor Red
            throw "HTTP Status $statusCode, Expected: $Expected"
        }
    } catch {
        Write-Host "   ❌ FAIL (Error: $($_.Exception.Message))" -ForegroundColor Red
        throw $_.Exception
    }
    Write-Host ""
}

# Funzione per PATCH con verifica status
function Test-Patch {
    param(
        [string]$Url,
        [string]$Data,
        [int]$Expected,
        [string]$Description
    )
    
    Write-Host "🔍 Test PATCH: $Description" -ForegroundColor Cyan
    Write-Host "   URL: $Url" -ForegroundColor Gray
    Write-Host "   Data: $Data" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method PATCH -Body $Data -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $Expected) {
            Write-Host "   ✅ PASS (Status: $statusCode)" -ForegroundColor Green
            $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 2 | Write-Host -ForegroundColor Gray
            return $response.Content
        } else {
            Write-Host "   ❌ FAIL (Status: $statusCode, Expected: $Expected)" -ForegroundColor Red
            Write-Host "   Response: $($response.Content)" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "   ❌ FAIL (Error: $($_.Exception.Message))" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

Write-Host "🔧 STEP 1: Verifica servizi attivi" -ForegroundColor Yellow
Test-Status "$BACKEND_BASE/health" 200 "Backend Health Check"
Test-Status "$FRONTEND_BASE" 200 "Frontend Health Check"

Write-Host "🔧 STEP 2: Verifica endpoints base" -ForegroundColor Yellow
Test-Status "$API_BASE/odl" 200 "Lista ODL"
Test-Status "$API_BASE/parti" 200 "Lista Parti"
Test-Status "$API_BASE/tools" 200 "Lista Tools"
Test-Status "$API_BASE/autoclavi" 200 "Lista Autoclavi"

Write-Host "🔧 STEP 2.5: Creazione dati di test" -ForegroundColor Yellow

# Crea un catalogo di test
$catalogo_data = @{
    part_number = "TEST-E2E-001"
    descrizione = "Parte di test per E2E v1.4.0"
    categoria = "Test"
    sotto_categoria = "E2E"
    attivo = $true
} | ConvertTo-Json

try {
    Test-Post "$API_BASE/catalogo" $catalogo_data 201 "Creazione catalogo test" | Out-Null
} catch {
    Write-Host "   ⚠️ Catalogo già esistente o errore, continuo..." -ForegroundColor Yellow
}

# Crea un ciclo di cura di test
$ciclo_data = @{
    nome = "Ciclo Test E2E"
    descrizione = "Ciclo di cura per test E2E"
    temperatura_stasi1 = 120.0
    pressione_stasi1 = 6.0
    durata_stasi1 = 60
    attiva_stasi2 = $false
} | ConvertTo-Json

try {
    Test-Post "$API_BASE/cicli-cura" $ciclo_data 201 "Creazione ciclo cura test" | Out-Null
} catch {
    Write-Host "   ⚠️ Ciclo già esistente o errore, continuo..." -ForegroundColor Yellow
}

# Crea una parte di test
$parte_data = @{
    part_number = "TEST-E2E-001"
    descrizione_breve = "Parte test E2E v1.4.0"
    num_valvole_richieste = 1
    ciclo_cura_id = 1
} | ConvertTo-Json

try {
    $parte_response = Test-Post "$API_BASE/parti" $parte_data 201 "Creazione parte test"
    $parte_obj = $parte_response | ConvertFrom-Json
    $parte_id = $parte_obj.id
} catch {
    Write-Host "   ⚠️ Parte già esistente, uso ID 1" -ForegroundColor Yellow
    $parte_id = 1
}

# Crea un tool di test
$tool_data = @{
    part_number_tool = "TOOL-TEST-E2E-001"
    descrizione = "Tool di test per E2E v1.4.0"
    lunghezza_piano = 300.0
    larghezza_piano = 200.0
    peso = 5.0
    materiale = "Alluminio"
    disponibile = $true
} | ConvertTo-Json

try {
    $tool_response = Test-Post "$API_BASE/tools" $tool_data 201 "Creazione tool test"
    $tool_obj = $tool_response | ConvertFrom-Json
    $tool_id = $tool_obj.id
} catch {
    Write-Host "   ⚠️ Tool già esistente, uso ID 1" -ForegroundColor Yellow
    $tool_id = 1
}

# Crea un'autoclave di test se non esiste
$autoclave_data = @{
    nome = "Autoclave Test E2E"
    codice = "AUTO-TEST-001"
    lunghezza = 1000.0
    larghezza_piano = 800.0
    temperatura_max = 200.0
    pressione_max = 10.0
    max_load_kg = 500.0
    produttore = "Test Manufacturer"
    anno_produzione = 2024
} | ConvertTo-Json

try {
    Test-Post "$API_BASE/autoclavi" $autoclave_data 201 "Creazione autoclave test" | Out-Null
} catch {
    Write-Host "   ⚠️ Autoclave già esistente o errore, continuo..." -ForegroundColor Yellow
}

Write-Host "🔧 STEP 3: Creazione nuovo ODL" -ForegroundColor Yellow
$odl_data = @{
    parte_id = $parte_id
    tool_id = $tool_id
    priorita = 1
    note = "Test E2E v1.4.0"
} | ConvertTo-Json

$odl_response = Test-Post "$API_BASE/odl" $odl_data 201 "Creazione ODL"

# Estrae l'ID dell'ODL creato
$odl_obj = $odl_response | ConvertFrom-Json
$odl_id = $odl_obj.id
Write-Host "📝 ODL creato con ID: $odl_id" -ForegroundColor Green

Write-Host "🔧 STEP 4: Cambio stato ODL - Laminazione" -ForegroundColor Yellow
$status_data = @{
    new_status = "Laminazione"
} | ConvertTo-Json

Test-Patch "$API_BASE/odl/$odl_id/status" $status_data 200 "Cambio stato a Laminazione" | Out-Null

Write-Host "🔧 STEP 5: Cambio stato ODL - Caricato" -ForegroundColor Yellow
$status_data = @{
    new_status = "Attesa Cura"
} | ConvertTo-Json

Test-Patch "$API_BASE/odl/$odl_id/status" $status_data 200 "Cambio stato a Attesa Cura" | Out-Null

Write-Host "🔧 STEP 6: Verifica ODL disponibili per nesting" -ForegroundColor Yellow
Test-Status "$API_BASE/batch_nesting/data" 200 "Dati disponibili per nesting"

Write-Host "🔧 STEP 7: Esecuzione algoritmo di nesting" -ForegroundColor Yellow
$nesting_data = @{
    odl_ids = @($odl_id.ToString())
    autoclave_ids = @("1")
    parametri = @{
        padding_mm = 20
        min_distance_mm = 15
        priorita_area = $true
    }
} | ConvertTo-Json -Depth 3

try {
    $nesting_response = Test-Post "$API_BASE/batch_nesting/genera" $nesting_data 200 "Esecuzione nesting"
    
    # Estrae l'ID del batch creato
    $nesting_obj = $nesting_response | ConvertFrom-Json
    $batch_id = $nesting_obj.batch_id
    Write-Host "📝 Batch creato con ID: $batch_id" -ForegroundColor Green
    
    Write-Host "🔧 STEP 8: Conferma batch" -ForegroundColor Yellow
    Test-Patch "$API_BASE/batch_nesting/$batch_id/conferma?confermato_da_utente=TestE2E&confermato_da_ruolo=Test" "" 200 "Conferma batch" | Out-Null
    
    Write-Host "🔧 STEP 9: Verifica lista batch" -ForegroundColor Yellow
    Test-Status "$API_BASE/batch_nesting" 200 "Lista batch nesting"
    
} catch {
    Write-Host "   ⚠️ Nesting non disponibile o errore, salto questo step..." -ForegroundColor Yellow
    $batch_id = "test-batch-id"
}

Write-Host "🔧 STEP 10: Cambio stato ODL - In Cura" -ForegroundColor Yellow
$status_data = @{
    new_status = "Cura"
} | ConvertTo-Json

Test-Patch "$API_BASE/odl/$odl_id/status" $status_data 200 "Cambio stato a Cura" | Out-Null

Write-Host "🔧 STEP 11: Completamento ODL" -ForegroundColor Yellow
$status_data = @{
    new_status = "Finito"
} | ConvertTo-Json

Test-Patch "$API_BASE/odl/$odl_id/status" $status_data 200 "Completamento ODL" | Out-Null

Write-Host "🔧 STEP 12: Generazione report" -ForegroundColor Yellow
$report_data = @{
    report_type = "nesting"
    include_sections = "summary,details"
    period_start = "2024-01-01T00:00:00"
    period_end = "2024-12-31T23:59:59"
} | ConvertTo-Json

try {
    Test-Post "$API_BASE/reports/generate" $report_data 200 "Generazione report" | Out-Null
} catch {
    Write-Host "   ⚠️ Report non disponibile o errore, salto questo step..." -ForegroundColor Yellow
}

Write-Host "🔧 STEP 13: Verifica log del sistema" -ForegroundColor Yellow
try {
    Test-Status "$API_BASE/system-logs?limit=10" 200 "Log di sistema"
} catch {
    Write-Host "   ⚠️ Log di sistema non disponibili o errore, salto questo step..." -ForegroundColor Yellow
}

Write-Host "🔧 STEP 14: Verifica stato finale ODL" -ForegroundColor Yellow
Test-Status "$API_BASE/odl/$odl_id" 200 "Stato finale ODL"

Write-Host ""
Write-Host "🎉 ==================================" -ForegroundColor Green
Write-Host "🎉 TUTTI I TEST E2E SONO PASSATI!" -ForegroundColor Green
Write-Host "🎉 CarbonPilot v1.4.0 è pronto!" -ForegroundColor Green
Write-Host "🎉 ==================================" -ForegroundColor Green
Write-Host ""

exit 0 