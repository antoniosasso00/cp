#!/usr/bin/env python3
"""
Script di test per verificare l'abilitazione dei dati reali nel modulo Nesting.

Questo script testa:
1. Endpoint GET /api/nesting/ restituisce dati reali
2. Tutti i campi sono popolati correttamente
3. Nessun fallback generico è presente nei dati
4. Ciclo cura è estratto correttamente dal primo ODL

Uso:
    python tools/test_nesting_real_data.py
"""

import requests
import json
import sys
from typing import Dict, List, Any

# Configurazione
API_BASE_URL = "http://localhost:8000/api"
NESTING_ENDPOINT = f"{API_BASE_URL}/v1/nesting/"

def test_nesting_api_connection() -> bool:
    """Testa la connessione all'API del nesting."""
    try:
        response = requests.get(NESTING_ENDPOINT, timeout=5)
        if response.status_code == 200:
            print("✅ Connessione API nesting: OK")
            return True
        else:
            print(f"❌ Errore API: {response.status_code}")
            print(f"   Risposta: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossibile connettersi al server backend")
        print("   Assicurati che il server sia avviato: cd backend && uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return False

def analyze_nesting_data(nesting_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analizza i dati del nesting per verificare la completezza."""
    analysis = {
        "total_nesting": len(nesting_list),
        "fields_populated": {},
        "real_data_found": {},
        "fallback_issues": []
    }
    
    # Campi che dovrebbero essere popolati con dati reali
    expected_fields = [
        "id", "created_at", "stato", "autoclave_nome", "ciclo_cura",
        "odl_inclusi", "odl_esclusi", "efficienza", "area_utilizzata",
        "area_totale", "peso_totale", "valvole_utilizzate", "valvole_totali",
        "motivi_esclusione"
    ]
    
    for field in expected_fields:
        analysis["fields_populated"][field] = 0
        analysis["real_data_found"][field] = 0
    
    for i, nesting in enumerate(nesting_list):
        print(f"\n📊 Analisi Nesting #{i+1} (ID: {nesting.get('id', 'N/A')[:8]}...)")
        
        for field in expected_fields:
            value = nesting.get(field)
            
            if value is not None:
                analysis["fields_populated"][field] += 1
                
                # Verifica che non ci siano fallback generici
                if isinstance(value, str):
                    if value in ["—", "🛠 Non disponibile", "N/A", ""]:
                        analysis["fallback_issues"].append(f"Nesting {i+1}: {field} = '{value}'")
                    else:
                        analysis["real_data_found"][field] += 1
                        print(f"   ✅ {field}: {value}")
                elif isinstance(value, (int, float)) and value > 0:
                    analysis["real_data_found"][field] += 1
                    print(f"   ✅ {field}: {value}")
                elif isinstance(value, list):
                    analysis["real_data_found"][field] += 1
                    print(f"   ✅ {field}: {len(value)} elementi")
                else:
                    print(f"   ⚠️ {field}: {value} (valore vuoto)")
            else:
                print(f"   ❌ {field}: Non presente")
    
    return analysis

def print_analysis_summary(analysis: Dict[str, Any]) -> None:
    """Stampa un riassunto dell'analisi."""
    print("\n" + "="*60)
    print("📋 RIASSUNTO ANALISI DATI REALI")
    print("="*60)
    
    total = analysis["total_nesting"]
    print(f"🔢 Totale nesting analizzati: {total}")
    
    if total == 0:
        print("⚠️ Nessun nesting trovato nel database")
        return
    
    print(f"\n📊 Campi Popolati (su {total} nesting):")
    for field, count in analysis["fields_populated"].items():
        percentage = (count / total) * 100 if total > 0 else 0
        status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
        print(f"   {status} {field}: {count}/{total} ({percentage:.1f}%)")
    
    print(f"\n🎯 Dati Reali Trovati (su {total} nesting):")
    for field, count in analysis["real_data_found"].items():
        percentage = (count / total) * 100 if total > 0 else 0
        status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
        print(f"   {status} {field}: {count}/{total} ({percentage:.1f}%)")
    
    if analysis["fallback_issues"]:
        print(f"\n🚨 Fallback Generici Trovati:")
        for issue in analysis["fallback_issues"]:
            print(f"   ❌ {issue}")
    else:
        print(f"\n✅ Nessun fallback generico trovato!")

def test_specific_improvements() -> None:
    """Testa le migliorie specifiche implementate."""
    print("\n" + "="*60)
    print("🔍 TEST MIGLIORIE SPECIFICHE")
    print("="*60)
    
    try:
        response = requests.get(NESTING_ENDPOINT)
        if response.status_code != 200:
            print("❌ Impossibile testare le migliorie - API non disponibile")
            return
        
        nesting_list = response.json()
        
        if not nesting_list:
            print("⚠️ Nessun nesting disponibile per testare le migliorie")
            return
        
        first_nesting = nesting_list[0]
        
        # Test 1: Ciclo cura non è più None hardcoded
        ciclo_cura = first_nesting.get("ciclo_cura")
        if ciclo_cura is not None and ciclo_cura != "None":
            print("✅ Ciclo cura: Estratto correttamente dal database")
        else:
            print("⚠️ Ciclo cura: Ancora None o non disponibile")
        
        # Test 2: Autoclave nome non è fallback generico
        autoclave_nome = first_nesting.get("autoclave_nome")
        if autoclave_nome and autoclave_nome not in ["—", "🛠 Non disponibile", "N/A"]:
            print("✅ Autoclave nome: Dati reali utilizzati")
        else:
            print("⚠️ Autoclave nome: Fallback o non disponibile")
        
        # Test 3: Motivi esclusione gestiti correttamente
        motivi_esclusione = first_nesting.get("motivi_esclusione")
        if isinstance(motivi_esclusione, list):
            print("✅ Motivi esclusione: Formato array corretto")
        else:
            print("⚠️ Motivi esclusione: Formato non corretto o non disponibile")
        
        # Test 4: Campi numerici popolati
        numeric_fields = ["odl_inclusi", "efficienza", "peso_totale", "valvole_utilizzate"]
        numeric_ok = 0
        for field in numeric_fields:
            value = first_nesting.get(field)
            if isinstance(value, (int, float)) and value >= 0:
                numeric_ok += 1
        
        if numeric_ok >= len(numeric_fields) // 2:
            print(f"✅ Campi numerici: {numeric_ok}/{len(numeric_fields)} popolati")
        else:
            print(f"⚠️ Campi numerici: Solo {numeric_ok}/{len(numeric_fields)} popolati")
            
    except Exception as e:
        print(f"❌ Errore durante il test delle migliorie: {e}")

def main():
    """Funzione principale del test."""
    print("🧪 TEST ABILITAZIONE DATI REALI - MODULO NESTING")
    print("="*60)
    
    # Test 1: Connessione API
    if not test_nesting_api_connection():
        sys.exit(1)
    
    # Test 2: Recupero e analisi dati
    try:
        response = requests.get(NESTING_ENDPOINT)
        nesting_list = response.json()
        
        print(f"\n📥 Dati ricevuti: {len(nesting_list)} nesting")
        
        if nesting_list:
            # Mostra esempio del primo nesting
            print(f"\n📋 Esempio primo nesting:")
            print(json.dumps(nesting_list[0], indent=2, ensure_ascii=False))
            
            # Analizza tutti i dati
            analysis = analyze_nesting_data(nesting_list)
            print_analysis_summary(analysis)
            
            # Test migliorie specifiche
            test_specific_improvements()
            
            # Verdetto finale
            total_fields = len(analysis["fields_populated"])
            populated_fields = sum(1 for count in analysis["real_data_found"].values() if count > 0)
            success_rate = (populated_fields / total_fields) * 100
            
            print(f"\n🎯 VERDETTO FINALE")
            print("="*30)
            if success_rate >= 80:
                print(f"✅ SUCCESSO: {success_rate:.1f}% dei campi utilizzano dati reali")
                print("   L'abilitazione dei dati reali è stata completata con successo!")
            elif success_rate >= 60:
                print(f"⚠️ PARZIALE: {success_rate:.1f}% dei campi utilizzano dati reali")
                print("   Alcune migliorie sono state applicate, ma c'è ancora lavoro da fare.")
            else:
                print(f"❌ FALLIMENTO: Solo {success_rate:.1f}% dei campi utilizzano dati reali")
                print("   Le modifiche non sono state applicate correttamente.")
                
        else:
            print("⚠️ Nessun nesting trovato nel database")
            print("   Crea alcuni nesting per testare completamente le modifiche")
            
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 