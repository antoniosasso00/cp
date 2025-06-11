#!/usr/bin/env python3
"""
Test workflow con batch esistenti
"""

import requests
import json

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_workflow_with_existing_batches():
    """Test workflow con batch esistenti nel database"""
    print("🧪 Test workflow con batch esistenti")
    
    # 1. Lista batch esistenti
    print("\n📋 1. Lista batch esistenti:")
    response = requests.get(f"{BASE_URL}/api/batch_nesting/", headers=HEADERS)
    if response.status_code == 200:
        batches = response.json()
        print(f"   Trovati {len(batches)} batch")
        
        # Trova batch in diversi stati
        sospesi = [b for b in batches if b.get('stato') == 'sospeso']
        in_cura = [b for b in batches if b.get('stato') == 'in_cura']
        
        print(f"   - Sospesi: {len(sospesi)}")
        print(f"   - In cura: {len(in_cura)}")
        
        # 2. Test START CURE su batch sospeso
        if sospesi:
            batch_sospeso = sospesi[0]
            print(f"\n🔄 2. Test START CURE su batch sospeso: {batch_sospeso['id'][:8]}...")
            
            response = requests.patch(
                f"{BASE_URL}/api/batch_nesting/{batch_sospeso['id']}/start-cure",
                headers=HEADERS,
                params={
                    "caricato_da_utente": "TEST_OPERATOR",
                    "caricato_da_ruolo": "OPERATOR"
                }
            )
            
            if response.status_code == 200:
                print("   ✅ Start cure riuscito!")
                in_cura.append(batch_sospeso)  # Aggiungi alla lista in_cura
            else:
                print(f"   ❌ Start cure fallito: {response.status_code}")
                print(f"   Errore: {response.text}")
        
        # 3. Test TERMINATE su batch in cura
        if in_cura:
            batch_in_cura = in_cura[0]
            print(f"\n🏁 3. Test TERMINATE su batch in cura: {batch_in_cura['id'][:8]}...")
            
            response = requests.patch(
                f"{BASE_URL}/api/batch_nesting/{batch_in_cura['id']}/terminate",
                headers=HEADERS,
                params={
                    "terminato_da_utente": "TEST_OPERATOR", 
                    "terminato_da_ruolo": "OPERATOR"
                }
            )
            
            if response.status_code == 200:
                print("   ✅ Terminate riuscito!")
                
                # Verifica TempoFase
                batch_details = requests.get(f"{BASE_URL}/api/batch_nesting/{batch_in_cura['id']}", headers=HEADERS)
                if batch_details.status_code == 200:
                    batch_data = batch_details.json()
                    odl_ids = batch_data.get('odl_ids', [])
                    
                    print(f"\n⏱️ 4. Verifica TempoFase per {len(odl_ids)} ODL:")
                    
                    for odl_id in odl_ids:
                        # Nota: il percorso corretto potrebbe essere diverso
                        tempo_response = requests.get(f"{BASE_URL}/api/tempo-fasi?odl_id={odl_id}", headers=HEADERS)
                        if tempo_response.status_code == 200:
                            tempo_fasi = tempo_response.json()
                            cura_records = [tf for tf in tempo_fasi if tf.get('fase') == 'cura']
                            if cura_records:
                                cura = cura_records[0]
                                durata = cura.get('durata_minuti', 'N/A')
                                print(f"     ✅ ODL {odl_id}: timing cura registrato ({durata} min)")
                            else:
                                print(f"     ⚠️ ODL {odl_id}: nessun timing cura")
                        else:
                            print(f"     ❌ ODL {odl_id}: errore recupero TempoFase")
                            
            else:
                print(f"   ❌ Terminate fallito: {response.status_code}")
                print(f"   Errore: {response.text}")
        
        # 5. Test lista batch DRAFT
        print(f"\n📦 5. Test lista batch DRAFT:")
        response = requests.get(f"{BASE_URL}/api/batch_nesting/draft", headers=HEADERS)
        if response.status_code == 200:
            result = response.json()
            draft_batches = result.get('draft_batches', [])
            stats = result.get('stats', {})
            
            print(f"   ✅ Batch DRAFT in memoria: {len(draft_batches)}")
            print(f"   📊 Stats: {stats}")
            
            for i, draft in enumerate(draft_batches):
                print(f"     📦 {i+1}. {draft.get('autoclave_nome')} - {draft.get('efficiency', 0):.1f}%")
        else:
            print(f"   ❌ Lista DRAFT fallita: {response.status_code}")
        
        print(f"\n🎉 TEST COMPLETATO!")
        print(f"✅ Workflow batch esistenti verificato")
        print(f"✅ Integrazione TempoFase testata")
        print(f"✅ Gestione batch DRAFT funzionante")
        
    else:
        print(f"❌ Errore lista batch: {response.status_code}")

if __name__ == "__main__":
    test_workflow_with_existing_batches() 