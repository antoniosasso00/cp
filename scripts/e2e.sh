#!/bin/bash

# Test End-to-End per CarbonPilot v1.4.0
# Flusso: ODL → laminazione → nesting → batch → cura → report

set -e  # Esce se un comando fallisce

API_BASE="http://localhost:8000/api"
FRONTEND_BASE="http://localhost:3000"

echo "🧪 Avvio test End-to-End CarbonPilot v1.4.0"
echo "=================================="

# Funzione per verificare status HTTP
check_status() {
    local url=$1
    local expected=$2
    local description=$3
    
    echo "🔍 Test: $description"
    echo "   URL: $url"
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url")
    
    if [ "$response" -eq "$expected" ]; then
        echo "   ✅ PASS (Status: $response)"
    else
        echo "   ❌ FAIL (Status: $response, Expected: $expected)"
        echo "   Response: $(cat /tmp/response.json)"
        exit 1
    fi
    echo ""
}

# Funzione per POST con verifica status
post_and_check() {
    local url=$1
    local data=$2
    local expected=$3
    local description=$4
    
    echo "🔍 Test POST: $description"
    echo "   URL: $url"
    echo "   Data: $data"
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$url")
    
    if [ "$response" -eq "$expected" ]; then
        echo "   ✅ PASS (Status: $response)"
        cat /tmp/response.json | head -3
    else
        echo "   ❌ FAIL (Status: $response, Expected: $expected)"
        echo "   Response: $(cat /tmp/response.json)"
        exit 1
    fi
    echo ""
}

echo "🔧 STEP 1: Verifica servizi attivi"
check_status "$API_BASE/health" 200 "Backend Health Check"
check_status "$FRONTEND_BASE" 200 "Frontend Health Check"

echo "🔧 STEP 2: Verifica endpoints base"
check_status "$API_BASE/odl" 200 "Lista ODL"
check_status "$API_BASE/parts" 200 "Lista Parti"
check_status "$API_BASE/tools" 200 "Lista Tools"
check_status "$API_BASE/autoclavi" 200 "Lista Autoclavi"

echo "🔧 STEP 3: Creazione nuovo ODL"
odl_data='{
    "parte_id": 1,
    "tool_id": 1,
    "priorita": 1,
    "note": "Test E2E v1.4.0"
}'
post_and_check "$API_BASE/odl" "$odl_data" 201 "Creazione ODL"

# Estrae l'ID dell'ODL creato
odl_id=$(cat /tmp/response.json | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "📝 ODL creato con ID: $odl_id"

echo "🔧 STEP 4: Cambio stato ODL - Laminazione"
status_data='{
    "nuovo_status": "Laminazione",
    "responsabile": "Test E2E",
    "note": "Cambio automatico da test E2E"
}'
post_and_check "$API_BASE/odl/$odl_id/status" "$status_data" 200 "Cambio stato a Laminazione"

echo "🔧 STEP 5: Cambio stato ODL - Caricato"
status_data='{
    "nuovo_status": "Caricato",
    "responsabile": "Test E2E",
    "note": "Pronto per nesting"
}'
post_and_check "$API_BASE/odl/$odl_id/status" "$status_data" 200 "Cambio stato a Caricato"

echo "🔧 STEP 6: Verifica ODL disponibili per nesting"
check_status "$API_BASE/nesting/odl-disponibili" 200 "ODL disponibili per nesting"

echo "🔧 STEP 7: Esecuzione algoritmo di nesting"
nesting_data='{
    "autoclave_id": 1,
    "odl_ids": ['$odl_id'],
    "use_secondary_plane": false
}'
post_and_check "$API_BASE/nesting/esegui" "$nesting_data" 200 "Esecuzione nesting"

# Estrae l'ID del nesting result
nesting_id=$(cat /tmp/response.json | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "📝 Nesting creato con ID: $nesting_id"

echo "🔧 STEP 8: Conferma nesting"
confirm_data='{
    "confermato_da_ruolo": "Test E2E"
}'
post_and_check "$API_BASE/nesting/$nesting_id/conferma" "$confirm_data" 200 "Conferma nesting"

echo "🔧 STEP 9: Creazione batch da nesting"
batch_data='{
    "nesting_id": '$nesting_id',
    "nome_batch": "Batch Test E2E v1.4.0",
    "note": "Batch automatico da test E2E"
}'
post_and_check "$API_BASE/nesting/crea-batch" "$batch_data" 200 "Creazione batch"

echo "🔧 STEP 10: Verifica lista nesting risultati"
check_status "$API_BASE/nesting/risultati" 200 "Lista nesting risultati"

echo "🔧 STEP 11: Cambio stato ODL - In Cura"
status_data='{
    "nuovo_status": "In Cura",
    "responsabile": "Test E2E",
    "note": "Avvio processo di cura"
}'
post_and_check "$API_BASE/odl/$odl_id/status" "$status_data" 200 "Cambio stato a In Cura"

echo "🔧 STEP 12: Completamento ODL"
status_data='{
    "nuovo_status": "Completato",
    "responsabile": "Test E2E",
    "note": "ODL completato con successo"
}'
post_and_check "$API_BASE/odl/$odl_id/status" "$status_data" 200 "Completamento ODL"

echo "🔧 STEP 13: Generazione report"
report_data='{
    "report_type": "nesting",
    "include_sections": "summary,details",
    "period_start": "2024-01-01T00:00:00",
    "period_end": "2024-12-31T23:59:59"
}'
post_and_check "$API_BASE/reports/generate" "$report_data" 200 "Generazione report"

echo "🔧 STEP 14: Verifica log del sistema"
check_status "$API_BASE/logs/system?limit=10" 200 "Log di sistema"

echo "🔧 STEP 15: Verifica stato finale ODL"
check_status "$API_BASE/odl/$odl_id" 200 "Stato finale ODL"

echo ""
echo "🎉 =================================="
echo "🎉 TUTTI I TEST E2E SONO PASSATI!"
echo "🎉 CarbonPilot v1.4.0 è pronto!"
echo "🎉 =================================="
echo ""

# Cleanup dei file temporanei
rm -f /tmp/response.json

exit 0 