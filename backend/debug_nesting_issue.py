#!/usr/bin/env python3
"""
Debug del problema di nesting che esclude tutti gli ODL
"""
import requests
import json
import sqlite3
from datetime import datetime

def debug_nesting_issue():
    """Analizza perché il nesting esclude tutti gli ODL"""
    
    print("🔍 DEBUG PROBLEMA NESTING")
    print("=" * 50)
    
    # 1. Analizza i dati nel database
    print("📋 1. ANALISI DATI DATABASE:")
    print("-" * 30)
    
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    # Controlla ODL con dettagli completi
    cursor.execute('''
        SELECT o.id, o.status, p.part_number, p.descrizione_breve, 
               t.part_number_tool, t.larghezza_piano, t.lunghezza_piano, t.peso,
               cc.nome as ciclo_cura, p.ciclo_cura_id
        FROM odl o
        JOIN parti p ON o.parte_id = p.id
        JOIN tools t ON o.tool_id = t.id
        LEFT JOIN cicli_cura cc ON p.ciclo_cura_id = cc.id
        WHERE o.status = 'Attesa Cura'
        ORDER BY o.id
    ''')
    
    odl_data = cursor.fetchall()
    print(f"ODL in 'Attesa Cura': {len(odl_data)}")
    
    for row in odl_data:
        print(f"  ODL #{row[0]}:")
        print(f"    Parte: {row[2]} ({row[3]})")
        print(f"    Tool: {row[4]} ({row[5]}x{row[6]}mm, {row[7]}kg)")
        print(f"    Ciclo: {row[8]} (ID: {row[9]})")
        print()
    
    # Controlla autoclavi
    cursor.execute('''
        SELECT id, nome, larghezza_piano, lunghezza, max_load_kg
        FROM autoclavi
        WHERE stato = 'DISPONIBILE'
        ORDER BY id
    ''')
    
    autoclave_data = cursor.fetchall()
    print(f"Autoclavi disponibili: {len(autoclave_data)}")
    
    for row in autoclave_data:
        print(f"  Autoclave #{row[0]}: {row[1]} ({row[2]}x{row[3]}mm, {row[4]}kg max)")
    
    conn.close()
    
    # 2. Testa l'algoritmo di nesting direttamente
    print("\n🧠 2. TEST ALGORITMO NESTING:")
    print("-" * 30)
    
    try:
        # Importa il servizio di nesting
        import sys
        sys.path.append('.')
        
        from services.nesting_service import NestingService, NestingParameters
        from api.database import get_db
        
        # Crea una sessione database
        db = next(get_db())
        
        # Crea il servizio
        nesting_service = NestingService()
        
        # Parametri di test
        odl_ids = [1, 2, 3]  # I primi 3 ODL
        autoclave_id = 1     # Prima autoclave
        parameters = NestingParameters(
            padding_mm=20,
            min_distance_mm=15,
            priorita_area=True
        )
        
        print(f"Test con ODL: {odl_ids}")
        print(f"Autoclave: {autoclave_id}")
        print(f"Parametri: {parameters}")
        
        # 1. Carica dati ODL
        print("\n📋 Caricamento dati ODL...")
        odl_data = nesting_service.get_odl_data(db, odl_ids)
        print(f"ODL caricati: {len(odl_data)}")
        
        for odl in odl_data:
            print(f"  ODL {odl['odl_id']}: {odl['tool_width']}x{odl['tool_height']}mm, {odl['tool_weight']}kg")
            print(f"    Ciclo: {odl['ciclo_cura_id']}")
        
        # 2. Carica dati autoclave
        print("\n🏭 Caricamento dati autoclave...")
        autoclave_data = nesting_service.get_autoclave_data(db, autoclave_id)
        print(f"Autoclave: {autoclave_data['nome']}")
        print(f"Dimensioni: {autoclave_data['larghezza_piano']}x{autoclave_data['lunghezza']}mm")
        print(f"Peso max: {autoclave_data['max_load_kg']}kg")
        
        # 3. Verifica compatibilità cicli
        print("\n🔄 Verifica compatibilità cicli...")
        compatible_odls, excluded_odls = nesting_service.check_ciclo_cura_compatibility(odl_data)
        print(f"ODL compatibili: {len(compatible_odls)}")
        print(f"ODL esclusi: {len(excluded_odls)}")
        
        if excluded_odls:
            print("Motivi esclusione:")
            for exc in excluded_odls:
                print(f"  ODL {exc['odl_id']}: {exc['motivo']} - {exc['dettagli']}")
        
        # 4. Esegui algoritmo di nesting
        if compatible_odls:
            print("\n🎯 Esecuzione algoritmo nesting...")
            nesting_result = nesting_service.perform_nesting_2d(
                compatible_odls, autoclave_data, parameters
            )
            
            print(f"Risultato algoritmo:")
            print(f"  Successo: {nesting_result.success}")
            print(f"  Status: {nesting_result.algorithm_status}")
            print(f"  Tool posizionati: {len(nesting_result.positioned_tools)}")
            print(f"  ODL esclusi: {len(nesting_result.excluded_odls)}")
            print(f"  Efficienza: {nesting_result.efficiency:.1f}%")
            
            if nesting_result.excluded_odls:
                print("Dettagli esclusioni:")
                for exc in nesting_result.excluded_odls:
                    print(f"  {exc}")
        else:
            print("❌ Nessun ODL compatibile trovato!")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 3. Controlla l'ultimo batch generato
    print("\n📦 3. ANALISI ULTIMO BATCH:")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8000/api/v1/batch_nesting/ef4e005d-cc35-43f2-b08e-b1240546aab3/full")
        if response.status_code == 200:
            batch_data = response.json()
            print(f"Batch ID: {batch_data.get('id', 'N/A')}")
            print(f"Nome: {batch_data.get('nome', 'N/A')}")
            print(f"Stato: {batch_data.get('stato', 'N/A')}")
            print(f"ODL inclusi: {len(batch_data.get('odl_ids', []))}")
            print(f"ODL esclusi: {len(batch_data.get('odl_esclusi', []))}")
            
            if batch_data.get('odl_esclusi'):
                print("Dettagli ODL esclusi:")
                for exc in batch_data.get('odl_esclusi', []):
                    print(f"  {exc}")
            
            # Controlla configurazione
            config = batch_data.get('configurazione_json', {})
            if config:
                print(f"Configurazione presente:")
                print(f"  Canvas: {config.get('canvas_width', 0)}x{config.get('canvas_height', 0)}")
                print(f"  Tool positions: {len(config.get('tool_positions', []))}")
            else:
                print("❌ Nessuna configurazione trovata")
        else:
            print(f"❌ Errore nel recupero batch: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore nella richiesta: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 DEBUG COMPLETATO")

if __name__ == "__main__":
    debug_nesting_issue() 