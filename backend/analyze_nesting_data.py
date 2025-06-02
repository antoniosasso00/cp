#!/usr/bin/env python3
"""
Analisi Dati Nesting Reali - CarbonPilot
Verifica la qualità e l'affidabilità dei dati di nesting nel database
"""

import sqlite3
import json
import requests
from datetime import datetime

def analyze_database_data():
    """Analizza i dati reali del database"""
    print("🔍 ANALISI DATI NESTING REALI - DATABASE")
    print("=" * 50)
    
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    try:
        # 1. Verifica ODL disponibili per nesting
        print("\n1️⃣ ANALISI ODL DISPONIBILI")
        cursor.execute("""
            SELECT o.id, o.status, p.part_number, p.descrizione_breve,
                   t.part_number_tool, t.larghezza_piano, t.lunghezza_piano, t.peso
            FROM odl o
            JOIN parti p ON o.parte_id = p.id  
            JOIN tools t ON o.tool_id = t.id
            WHERE o.status IN ('Attesa Cura', 'Preparazione')
            ORDER BY o.id
        """)
        
        odl_data = cursor.fetchall()
        print(f"📋 ODL disponibili per nesting: {len(odl_data)}")
        
        if odl_data:
            print("\n📊 Dettagli ODL:")
            total_area = 0
            total_weight = 0
            for odl in odl_data[:10]:  # Primi 10
                area = (odl[5] or 0) * (odl[6] or 0)
                total_area += area
                total_weight += (odl[7] or 0)
                print(f"   ODL {odl[0]}: {odl[2]} | Tool: {odl[4]} | {odl[5]}x{odl[6]}mm | {odl[7]}kg | Area: {area/10000:.2f}cm²")
            
            print(f"\n📈 Statistiche aggregate:")
            print(f"   Area totale tools: {total_area/10000:.2f} cm²")
            print(f"   Peso totale: {total_weight:.1f} kg")
        
        # 2. Verifica autoclavi disponibili
        print("\n2️⃣ ANALISI AUTOCLAVI DISPONIBILI")
        cursor.execute("""
            SELECT id, nome, codice, stato, lunghezza, larghezza_piano, 
                   max_load_kg, num_linee_vuoto
            FROM autoclavi 
            WHERE stato = 'DISPONIBILE'
        """)
        
        autoclavi_data = cursor.fetchall()
        print(f"🏭 Autoclavi disponibili: {len(autoclavi_data)}")
        
        if autoclavi_data:
            for autoclave in autoclavi_data:
                area_piano = (autoclave[4] or 0) * (autoclave[5] or 0)
                print(f"   {autoclave[1]}: {autoclave[5]}x{autoclave[4]}mm | {autoclave[6]}kg max | {autoclave[7]} linee | Area: {area_piano/10000:.2f}cm²")
        
        # 3. Analisi nesting results esistenti
        print("\n3️⃣ ANALISI NESTING RESULTS ESISTENTI")
        cursor.execute("""
            SELECT nr.id, nr.stato, nr.area_utilizzata, nr.area_totale,
                   nr.peso_totale_kg, nr.valvole_utilizzate, nr.valvole_totali,
                   a.nome as autoclave_nome, nr.created_at
            FROM nesting_results nr
            LEFT JOIN autoclavi a ON nr.autoclave_id = a.id
            ORDER BY nr.created_at DESC
            LIMIT 10
        """)
        
        nesting_results = cursor.fetchall()
        print(f"📊 Nesting results nel database: {len(nesting_results)}")
        
        if nesting_results:
            print("\n🔍 Ultimi nesting results:")
            for nr in nesting_results:
                # Calcola efficienza area
                efficienza_area = 0
                if nr[3] and nr[3] > 0:  # area_totale
                    efficienza_area = (nr[2] / nr[3]) * 100  # area_utilizzata / area_totale
                
                # Calcola efficienza valvole
                efficienza_valvole = 0
                if nr[6] and nr[6] > 0:  # valvole_totali
                    efficienza_valvole = (nr[5] / nr[6]) * 100  # valvole_utilizzate / valvole_totali
                
                print(f"   ID {nr[0]} | {nr[1]} | {nr[7]} | Area: {efficienza_area:.1f}% | Valvole: {efficienza_valvole:.1f}% | Peso: {nr[4]}kg")
        
        # 4. Verifica batch nesting
        print("\n4️⃣ ANALISI BATCH NESTING")
        cursor.execute("""
            SELECT id, nome, stato, peso_totale_kg, area_totale_utilizzata,
                   valvole_totali_utilizzate, efficiency, created_at
            FROM batch_nesting
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        batch_data = cursor.fetchall()
        print(f"📦 Batch nesting nel database: {len(batch_data)}")
        
        if batch_data:
            print("\n🔍 Ultimi batch nesting:")
            for batch in batch_data:
                print(f"   {batch[1][:30]} | {batch[2]} | Peso: {batch[3]}kg | Area: {batch[4]}cm² | Efficienza: {batch[6]:.1f}%")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore nell'analisi database: {e}")
        conn.close()
        return False

def test_api_endpoints():
    """Testa gli endpoint API per verificare la coerenza dei dati"""
    print("\n🌐 TEST ENDPOINT API")
    print("=" * 30)
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Test endpoint /data
        print("\n📡 Test /batch_nesting/data:")
        response = requests.get(f"{base_url}/batch_nesting/data", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            odl_count = len(data.get('odl_in_attesa_cura', []))
            autoclavi_count = len(data.get('autoclavi_disponibili', []))
            
            print(f"   ✅ Endpoint funzionante")
            print(f"   📋 ODL disponibili: {odl_count}")
            print(f"   🏭 Autoclavi disponibili: {autoclavi_count}")
            
            # Analizza primo ODL se presente
            if data.get('odl_in_attesa_cura'):
                first_odl = data['odl_in_attesa_cura'][0]
                tool_data = first_odl.get('tool', {})
                print(f"   🔧 Primo ODL - Tool: {tool_data.get('larghezza_piano')}x{tool_data.get('lunghezza_piano')}mm, {tool_data.get('peso')}kg")
                
            # Analizza prima autoclave se presente
            if data.get('autoclavi_disponibili'):
                first_autoclave = data['autoclavi_disponibili'][0]
                print(f"   🏭 Prima autoclave: {first_autoclave.get('nome')} - {first_autoclave.get('larghezza_piano')}x{first_autoclave.get('lunghezza')}mm")
                
        else:
            print(f"   ❌ Errore endpoint: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Errore connessione API: {e}")

def test_nesting_calculation():
    """Testa i calcoli di nesting con dati reali"""
    print("\n🧮 TEST CALCOLI NESTING")
    print("=" * 30)
    
    # Esempio di calcolo manuale efficienza
    # Simuliamo i dati dell'interfaccia
    esempio_autoclave = {
        "larghezza_piano": 1500,  # mm
        "lunghezza": 2000,        # mm
        "area_totale": 1500 * 2000,  # mm²
        "area_totale_cm2": (1500 * 2000) / 100  # cm²
    }
    
    esempio_tools = [
        {"width": 450, "height": 450, "area": 450 * 450},  # Tool 1
        {"width": 400, "height": 350, "area": 400 * 350},  # Tool 2
    ]
    
    area_utilizzata_mm2 = sum(tool["area"] for tool in esempio_tools)
    area_utilizzata_cm2 = area_utilizzata_mm2 / 100
    
    efficienza_calcolata = (area_utilizzata_mm2 / esempio_autoclave["area_totale"]) * 100
    
    print(f"\n📐 CALCOLO ESEMPIO:")
    print(f"   Autoclave: {esempio_autoclave['larghezza_piano']}x{esempio_autoclave['lunghezza']}mm")
    print(f"   Area autoclave: {esempio_autoclave['area_totale_cm2']:.0f} cm²")
    print(f"   Tools posizionati: {len(esempio_tools)}")
    print(f"   Area utilizzata: {area_utilizzata_cm2:.2f} cm²")
    print(f"   Efficienza calcolata: {efficienza_calcolata:.1f}%")
    
    print(f"\n🔍 VERIFICA COERENZA:")
    if 40 <= efficienza_calcolata <= 60:
        print(f"   ✅ Efficienza nell'intervallo realistico (40-60%)")
    else:
        print(f"   ⚠️ Efficienza fuori dall'intervallo tipico")

def analyze_efficiency_discrepancies():
    """Analizza le discrepanze nei calcoli di efficienza"""
    print("\n⚖️ ANALISI DISCREPANZE EFFICIENZA")
    print("=" * 40)
    
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    try:
        # Verifica calcoli su batch esistenti
        cursor.execute("""
            SELECT bn.id, bn.nome, bn.area_totale_utilizzata, bn.efficiency,
                   a.larghezza_piano, a.lunghezza
            FROM batch_nesting bn
            JOIN autoclavi a ON bn.autoclave_id = a.id
            WHERE bn.area_totale_utilizzata > 0
            ORDER BY bn.created_at DESC
            LIMIT 5
        """)
        
        batch_results = cursor.fetchall()
        
        if batch_results:
            print("\n🔍 Verifica calcoli batch esistenti:")
            
            for batch in batch_results:
                batch_id, nome, area_utilizzata_cm2, efficiency_db, larghezza, lunghezza = batch
                
                # Calcola efficienza manualmente
                area_totale_mm2 = larghezza * lunghezza
                area_totale_cm2 = area_totale_mm2 / 100
                area_utilizzata_mm2 = area_utilizzata_cm2 * 100
                
                efficienza_calcolata = (area_utilizzata_mm2 / area_totale_mm2) * 100
                discrepanza = abs(efficiency_db - efficienza_calcolata)
                
                print(f"\n   📦 {nome[:30]}")
                print(f"      Autoclave: {larghezza}x{lunghezza}mm ({area_totale_cm2:.0f} cm²)")
                print(f"      Area utilizzata: {area_utilizzata_cm2:.2f} cm²")
                print(f"      Efficienza DB: {efficiency_db:.1f}%")
                print(f"      Efficienza calcolata: {efficienza_calcolata:.1f}%")
                print(f"      Discrepanza: {discrepanza:.1f}%")
                
                if discrepanza > 5:
                    print(f"      ⚠️ DISCREPANZA SIGNIFICATIVA!")
                else:
                    print(f"      ✅ Calcolo coerente")
        
    except Exception as e:
        print(f"❌ Errore nell'analisi discrepanze: {e}")
    finally:
        conn.close()

def main():
    """Funzione principale"""
    print("🔬 ANALISI COMPLETA DATI NESTING - CarbonPilot")
    print("=" * 60)
    print(f"Avviata alle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Analisi database
    db_ok = analyze_database_data()
    
    # Test API (se database OK)
    if db_ok:
        test_api_endpoints()
        test_nesting_calculation()
        analyze_efficiency_discrepancies()
    
    print("\n" + "=" * 60)
    print("🎯 RACCOMANDAZIONI:")
    print("1. Verificare che i tool abbiano dimensioni reali (non zero)")
    print("2. Controllare che i calcoli di efficienza usino le stesse unità di misura")
    print("3. Assicurarsi che l'algoritmo OR-Tools usi dati dal database, non mockup")
    print("4. Verificare che le esclusioni ODL abbiano motivi validi")
    print("5. Controllare che i parametri dell'autoclave siano corretti")

if __name__ == "__main__":
    main() 