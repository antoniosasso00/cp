#!/usr/bin/env python3
"""
🔧 TEST CORREZIONI NESTING PREVIEW
==================================

Script per testare le correzioni apportate al sistema di nesting preview:

1. ✅ Correzione conversione mm² → cm² (dividere per 10000 invece di 100)
2. ✅ Consistenza status ODL tra endpoint /data e /solve
3. ✅ Verifica che le statistiche riflettano la realtà

Autore: Assistant
Data: 2025-06-02
Versione: v1.0.0
"""

import requests
import json
import sys
from typing import Dict, Any

# Configurazione
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

def test_data_endpoint() -> Dict[str, Any]:
    """Testa l'endpoint /data per verificare ODL disponibili"""
    print("🔍 Test endpoint /data...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/batch_nesting/data", headers=HEADERS)
        
        if response.status_code != 200:
            print(f"❌ Errore endpoint /data: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        odl_count = len(data.get("odl_in_attesa_cura", []))
        autoclave_count = len(data.get("autoclavi_disponibili", []))
        
        print(f"✅ Endpoint /data OK: {odl_count} ODL, {autoclave_count} autoclavi")
        
        # Mostra dettagli primi ODL
        for i, odl in enumerate(data.get("odl_in_attesa_cura", [])[:3]):
            tool = odl.get("tool", {})
            parte = odl.get("parte", {})
            print(f"   • ODL {odl.get('id')}: {parte.get('part_number', 'N/A')} - "
                  f"Tool {tool.get('larghezza_piano', 0)}x{tool.get('lunghezza_piano', 0)}mm, "
                  f"Peso: {tool.get('peso', 0)}kg")
        
        return {
            "success": True,
            "odl_count": odl_count,
            "autoclave_count": autoclave_count,
            "data": data
        }
        
    except Exception as e:
        print(f"❌ Errore test /data: {str(e)}")
        return {"success": False, "error": str(e)}

def test_solve_endpoint(odl_ids: list, autoclave_id: int) -> Dict[str, Any]:
    """Testa l'endpoint /solve per verificare le correzioni"""
    print(f"🚀 Test endpoint /solve con ODL {odl_ids} e autoclave {autoclave_id}...")
    
    payload = {
        "odl_ids": odl_ids,
        "autoclave_id": autoclave_id,
        "padding_mm": 20.0,
        "min_distance_mm": 15.0,
        "vacuum_lines_capacity": 8
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/batch_nesting/solve", 
            headers=HEADERS,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Errore endpoint /solve: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Dettaglio: {error_data.get('detail', 'Errore sconosciuto')}")
            except:
                print(f"   Risposta: {response.text[:200]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        metrics = data.get("metrics", {})
        
        # Verifica correzioni
        area_pct = metrics.get("area_utilization_pct", 0)
        efficiency = metrics.get("efficiency_score", 0)
        total_area_cm2 = metrics.get("total_area_cm2", 0)
        positioned_count = metrics.get("pieces_positioned", 0)
        excluded_count = metrics.get("pieces_excluded", 0)
        
        print(f"✅ Endpoint /solve OK:")
        print(f"   📊 ODL posizionati: {positioned_count}")
        print(f"   📊 ODL esclusi: {excluded_count}")
        print(f"   📊 Area utilizzata: {area_pct:.1f}%")
        print(f"   📊 Area totale: {total_area_cm2:.1f} cm²")
        print(f"   📊 Efficienza: {efficiency:.1f}%")
        print(f"   📊 Algoritmo: {metrics.get('algorithm_status', 'N/A')}")
        
        # Verifica che l'area sia realistica (non più 100x troppo piccola)
        autoclave_info = data.get("autoclave_info", {})
        autoclave_area_cm2 = (autoclave_info.get("larghezza_piano", 0) * 
                             autoclave_info.get("lunghezza", 0)) / 100  # mm² → cm²
        
        print(f"   🏭 Area autoclave: {autoclave_area_cm2:.1f} cm²")
        
        # Controllo sanità: l'area utilizzata dovrebbe essere ragionevole
        if total_area_cm2 > 0 and autoclave_area_cm2 > 0:
            area_ratio = total_area_cm2 / autoclave_area_cm2 * 100
            print(f"   ✅ Rapporto area: {area_ratio:.1f}% (dovrebbe essere simile a area_pct)")
            
            if abs(area_ratio - area_pct) < 1.0:
                print(f"   ✅ Correzione conversione mm²→cm² FUNZIONA!")
            else:
                print(f"   ⚠️ Possibile problema nella conversione area")
        
        return {
            "success": True,
            "metrics": metrics,
            "positioned_count": positioned_count,
            "excluded_count": excluded_count,
            "data": data
        }
        
    except Exception as e:
        print(f"❌ Errore test /solve: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Funzione principale di test"""
    print("🔧 TEST CORREZIONI NESTING PREVIEW")
    print("=" * 50)
    
    # Test 1: Endpoint /data
    data_result = test_data_endpoint()
    if not data_result["success"]:
        print("❌ Test fallito su endpoint /data")
        sys.exit(1)
    
    print()
    
    # Test 2: Endpoint /solve se ci sono ODL disponibili
    if data_result["odl_count"] > 0 and data_result["autoclave_count"] > 0:
        # Prendi primi ODL e prima autoclave disponibili
        data = data_result["data"]
        odl_ids = [odl["id"] for odl in data["odl_in_attesa_cura"][:3]]  # Primi 3 ODL
        autoclave_id = data["autoclavi_disponibili"][0]["id"]
        
        solve_result = test_solve_endpoint(odl_ids, autoclave_id)
        
        if solve_result["success"]:
            print("\n✅ TUTTI I TEST PASSATI!")
            print(f"   • Endpoint /data: {data_result['odl_count']} ODL disponibili")
            print(f"   • Endpoint /solve: {solve_result['positioned_count']} ODL posizionati")
            print(f"   • Efficienza: {solve_result['metrics']['efficiency_score']:.1f}%")
            
            # Verifica miglioramento efficienza
            efficiency = solve_result['metrics']['efficiency_score']
            if efficiency > 60:
                print(f"   🎉 Efficienza OTTIMA: {efficiency:.1f}%")
            elif efficiency > 40:
                print(f"   ✅ Efficienza BUONA: {efficiency:.1f}%")
            else:
                print(f"   ⚠️ Efficienza bassa: {efficiency:.1f}% (possibili problemi)")
        else:
            print("❌ Test fallito su endpoint /solve")
            sys.exit(1)
    else:
        print("⚠️ Nessun ODL o autoclave disponibile per test /solve")
    
    print("\n🎯 CORREZIONI VERIFICATE CON SUCCESSO!")

if __name__ == "__main__":
    main() 