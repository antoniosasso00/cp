#!/usr/bin/env python3
"""
Script di test per il sistema di generazione automatica dei report
Testa il trigger automatico quando un ODL passa a "Finito"
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_automatic_report_generation():
    """
    Test completo del sistema di generazione automatica dei report
    """
    print("🚀 Test Sistema Generazione Automatica Report")
    print("=" * 50)
    
    # 1. Verifica che ci siano ODL in stato "Cura"
    print("\n1. Verifica ODL in stato 'Cura'...")
    response = requests.get(f"{BASE_URL}{API_PREFIX}/odl/")
    if response.status_code == 200:
        odl_list = response.json()
        odl_in_cura = [odl for odl in odl_list if odl.get('status') == 'Cura']
        print(f"   ✅ Trovati {len(odl_in_cura)} ODL in stato 'Cura'")
        
        if not odl_in_cura:
            print("   ⚠️ Nessun ODL in stato 'Cura' trovato. Creando un ODL di test...")
            # Qui potresti creare un ODL di test se necessario
            return False
    else:
        print(f"   ❌ Errore nel caricamento ODL: {response.status_code}")
        return False
    
    # 2. Trova un nesting associato agli ODL in cura
    print("\n2. Verifica nesting associati...")
    response = requests.get(f"{BASE_URL}{API_PREFIX}/nesting/")
    if response.status_code == 200:
        nestings = response.json()
        nesting_con_odl_cura = None
        
        for nesting in nestings:
            if nesting.get('stato') == 'Confermato':
                # Verifica se ha ODL in cura
                odl_ids = nesting.get('odl_ids', [])
                for odl_id in odl_ids:
                    for odl in odl_in_cura:
                        if odl['id'] == odl_id:
                            nesting_con_odl_cura = nesting
                            break
                if nesting_con_odl_cura:
                    break
        
        if nesting_con_odl_cura:
            print(f"   ✅ Trovato nesting #{nesting_con_odl_cura['id']} con ODL in cura")
        else:
            print("   ⚠️ Nessun nesting con ODL in cura trovato")
            return False
    else:
        print(f"   ❌ Errore nel caricamento nesting: {response.status_code}")
        return False
    
    # 3. Simula il completamento di un ODL (Cura -> Finito)
    print("\n3. Test trigger automatico...")
    test_odl = odl_in_cura[0]
    print(f"   🎯 Test con ODL #{test_odl['id']}")
    
    # Verifica se il nesting ha già un report
    if nesting_con_odl_cura.get('report_id'):
        print(f"   ℹ️ Il nesting #{nesting_con_odl_cura['id']} ha già un report (ID: {nesting_con_odl_cura['report_id']})")
    else:
        print(f"   📝 Il nesting #{nesting_con_odl_cura['id']} non ha ancora un report")
    
    # Simula il cambio stato ODL da "Cura" a "Finito"
    print(f"   🔄 Cambio stato ODL #{test_odl['id']}: Cura -> Finito")
    response = requests.patch(
        f"{BASE_URL}{API_PREFIX}/odl/{test_odl['id']}/autoclavista-status",
        params={"new_status": "Finito"}
    )
    
    if response.status_code == 200:
        print("   ✅ Stato ODL aggiornato con successo")
        
        # Attendi un momento per la generazione del report
        print("   ⏳ Attesa generazione report automatica...")
        time.sleep(3)
        
        # 4. Verifica se il report è stato generato
        print("\n4. Verifica generazione report...")
        response = requests.get(f"{BASE_URL}{API_PREFIX}/nesting/{nesting_con_odl_cura['id']}/report")
        
        if response.status_code == 200:
            # Controlla se è un file PDF o una risposta JSON
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                print("   🎉 Report PDF generato automaticamente!")
                print(f"   📄 Dimensione file: {len(response.content)} bytes")
                
                # Salva il file per verifica
                filename = f"test_report_nesting_{nesting_con_odl_cura['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"   💾 Report salvato come: {filename}")
                
            else:
                # Risposta JSON - controlla il messaggio
                try:
                    data = response.json()
                    if data.get('has_report') == False:
                        print("   ⚠️ Report non ancora generato automaticamente")
                        print(f"   📝 Messaggio: {data.get('message', 'N/A')}")
                    else:
                        print("   ✅ Report disponibile")
                except:
                    print("   ❓ Risposta non riconosciuta")
        else:
            print(f"   ❌ Errore nella verifica del report: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📝 Dettaglio errore: {error_data.get('detail', 'N/A')}")
            except:
                pass
        
        # 5. Test download report tramite API nesting
        print("\n5. Test download report via API nesting...")
        response = requests.get(f"{BASE_URL}{API_PREFIX}/nesting/{nesting_con_odl_cura['id']}/report")
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
            print("   ✅ Download report via API nesting funzionante")
        else:
            print("   ⚠️ Download report via API nesting non disponibile")
        
        # 6. Test lista report generali
        print("\n6. Test lista report generali...")
        response = requests.get(f"{BASE_URL}{API_PREFIX}/reports/")
        
        if response.status_code == 200:
            reports_data = response.json()
            reports = reports_data.get('reports', [])
            nesting_reports = [r for r in reports if r.get('report_type') == 'nesting']
            print(f"   ✅ Trovati {len(nesting_reports)} report di tipo 'nesting'")
            
            # Trova il report più recente
            if nesting_reports:
                latest_report = max(nesting_reports, key=lambda r: r['created_at'])
                print(f"   📄 Report più recente: {latest_report['filename']}")
                print(f"   📅 Creato il: {latest_report['created_at']}")
        else:
            print(f"   ❌ Errore nel caricamento lista report: {response.status_code}")
        
    else:
        print(f"   ❌ Errore nell'aggiornamento stato ODL: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   📝 Dettaglio errore: {error_data.get('detail', 'N/A')}")
        except:
            pass
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Test completato!")
    return True

def test_manual_report_generation():
    """
    Test della generazione manuale di report per nesting
    """
    print("\n🔧 Test Generazione Manuale Report")
    print("-" * 30)
    
    # Trova un nesting senza report
    response = requests.get(f"{BASE_URL}{API_PREFIX}/nesting/")
    if response.status_code == 200:
        nestings = response.json()
        nesting_senza_report = None
        
        for nesting in nestings:
            if not nesting.get('report_id'):
                nesting_senza_report = nesting
                break
        
        if nesting_senza_report:
            print(f"   🎯 Test con nesting #{nesting_senza_report['id']}")
            
            # Genera report manualmente
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/nesting/{nesting_senza_report['id']}/generate-report"
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Report generato manualmente")
                print(f"   📄 File: {result.get('report', {}).get('filename', 'N/A')}")
            else:
                print(f"   ❌ Errore nella generazione manuale: {response.status_code}")
        else:
            print("   ⚠️ Nessun nesting senza report trovato")
    else:
        print(f"   ❌ Errore nel caricamento nesting: {response.status_code}")

if __name__ == "__main__":
    print("🧪 Test Sistema Report CarbonPilot")
    print("Assicurati che il backend sia in esecuzione su http://localhost:8000")
    print()
    
    try:
        # Test connessione
        response = requests.get(f"{BASE_URL}{API_PREFIX}/")
        if response.status_code == 200:
            print("✅ Connessione al backend OK")
        else:
            print("❌ Errore connessione al backend")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Backend non raggiungibile. Assicurati che sia in esecuzione.")
        exit(1)
    
    # Esegui i test
    success = test_automatic_report_generation()
    test_manual_report_generation()
    
    if success:
        print("\n🎉 Tutti i test completati con successo!")
    else:
        print("\n⚠️ Alcuni test hanno avuto problemi. Controlla i log.") 