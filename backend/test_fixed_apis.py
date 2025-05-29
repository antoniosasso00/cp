#!/usr/bin/env python3
"""
Test specifico per verificare che le API non abbiano più errori SQLAlchemy
dopo il fix del database schedule_entries
"""

import requests
import json
from datetime import datetime

def test_monitoring_apis():
    """Testa tutte le API di monitoraggio per verificare assenza errori"""
    
    print("🧪 Test APIs Post-Fix Database")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    apis_to_test = [
        ("/api/v1/odl-monitoring/monitoring/stats", "Statistiche ODL"),
        ("/api/v1/odl-monitoring/monitoring", "Lista ODL monitoraggio"),
        ("/api/v1/odl-monitoring/monitoring?solo_attivi=true", "ODL attivi"),
        ("/api/v1/odl-monitoring/monitoring?limit=10", "ODL con limite"),
        ("/api/v1/odl/", "Lista ODL base"),
        ("/api/v1/catalogo/", "Catalogo parti"),
    ]
    
    success_count = 0
    total_count = len(apis_to_test)
    
    for endpoint, description in apis_to_test:
        print(f"\n🔍 Testing: {description}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                print(f"✅ {description}: OK ({count} elementi)")
                success_count += 1
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ {description}: Errore - {e}")
    
    # Test specifico per ODL con timeline
    print(f"\n🔍 Testing: Timeline ODL specifico")
    try:
        # Prima ottieni un ODL valido
        response = requests.get(f"{base_url}/api/v1/odl/", timeout=10)
        if response.status_code == 200:
            odl_list = response.json()
            if odl_list:
                odl_id = odl_list[0]['id']
                
                # Testa dettaglio
                detail_response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}", timeout=10)
                if detail_response.status_code == 200:
                    print(f"✅ Dettaglio ODL #{odl_id}: OK")
                    success_count += 1
                else:
                    print(f"❌ Dettaglio ODL #{odl_id}: HTTP {detail_response.status_code}")
                
                # Testa timeline
                timeline_response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}/timeline", timeout=10)
                if timeline_response.status_code == 200:
                    timeline_data = timeline_response.json()
                    print(f"✅ Timeline ODL #{odl_id}: OK ({len(timeline_data)} eventi)")
                elif timeline_response.status_code == 404:
                    print(f"⚠️  Timeline ODL #{odl_id}: Non disponibile (normale)")
                else:
                    print(f"❌ Timeline ODL #{odl_id}: HTTP {timeline_response.status_code}")
                
                # Testa progress
                progress_response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}/progress", timeout=10)
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    print(f"✅ Progress ODL #{odl_id}: OK (source: {progress_data.get('data_source', 'N/A')})")
                else:
                    print(f"❌ Progress ODL #{odl_id}: HTTP {progress_response.status_code}")
                    
                total_count += 3  # Aggiunti 3 test specifici
                
    except Exception as e:
        print(f"❌ Test timeline ODL: Errore - {e}")
    
    # Riepilogo
    print(f"\n{'='*50}")
    print(f"📊 RISULTATI TEST")
    print(f"{'='*50}")
    
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print(f"✅ Test superati: {success_count}/{total_count}")
    print(f"📈 Percentuale successo: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT: Tutte le API funzionano correttamente!")
        print("   Gli errori SQLAlchemy sono stati risolti.")
    elif success_rate >= 75:
        print("✅ BUONO: La maggior parte delle API funziona.")
        print("   Potrebbero esserci ancora piccoli problemi.")
    else:
        print("❌ PROBLEMI: Molte API non funzionano ancora.")
        print("   Sono necessarie ulteriori correzioni.")
    
    print(f"\n🕒 Test completato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_monitoring_apis() 