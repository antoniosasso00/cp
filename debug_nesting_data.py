#!/usr/bin/env python3
"""
🔍 SCRIPT DEBUG DATI NESTING
===============================

Questo script analizza i dati del nesting esistenti per identificare
il problema nella visualizzazione del frontend.
"""

import sqlite3
import json
import requests
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_database_data():
    """Controlla i dati nel database"""
    print_header("ANALISI DATI DATABASE")
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # 1. Controlla batch nesting
        print("\n📋 BATCH NESTING:")
        cursor.execute("""
            SELECT id, nome, stato, autoclave_id, configurazione_json, odl_ids 
            FROM batch_nesting 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        
        batches = cursor.fetchall()
        for batch in batches:
            batch_id, nome, stato, autoclave_id, config_json, odl_ids = batch
            print(f"  🆔 ID: {batch_id}")
            print(f"  📝 Nome: {nome}")
            print(f"  🔄 Stato: {stato}")
            print(f"  🏭 Autoclave ID: {autoclave_id}")
            print(f"  📊 ODL IDs: {odl_ids}")
            
            if config_json:
                try:
                    config = json.loads(config_json)
                    print(f"  🎯 Tool Positions: {len(config.get('tool_positions', []))}")
                    print(f"  📐 Canvas Size: {config.get('canvas_width', 'N/A')} x {config.get('canvas_height', 'N/A')}")
                    
                    # Mostra i primi 2 tool
                    for i, tool in enumerate(config.get('tool_positions', [])[:2]):
                        print(f"    Tool {i+1}: ODL {tool.get('odl_id')}, "
                              f"Size: {tool.get('width')}x{tool.get('height')}, "
                              f"Pos: ({tool.get('x')}, {tool.get('y')})")
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ Errore JSON: {e}")
            else:
                print(f"  ❌ Configurazione JSON: NULL")
            print("-" * 40)
        
        # 2. Controlla autoclavi
        print("\n🏭 AUTOCLAVI:")
        cursor.execute("""
            SELECT id, nome, codice, larghezza_piano, lunghezza, stato
            FROM autoclavi
            ORDER BY id
        """)
        
        autoclavi = cursor.fetchall()
        for autoclave in autoclavi:
            autoclave_id, nome, codice, larghezza, lunghezza, stato = autoclave
            print(f"  🆔 ID: {autoclave_id} - {nome} ({codice})")
            print(f"  📐 Dimensioni: {lunghezza} x {larghezza} mm")
            print(f"  🔄 Stato: {stato}")
            print("-" * 40)
        
        # 3. Controlla ODL associati
        print("\n📦 ODL ASSOCIATI:")
        if batches:
            batch_id = batches[0][0]
            odl_ids_json = batches[0][5]
            
            if odl_ids_json:
                try:
                    odl_ids = json.loads(odl_ids_json)
                    placeholders = ','.join('?' * len(odl_ids))
                    cursor.execute(f"""
                        SELECT o.id, o.status, p.part_number, t.part_number_tool, 
                               t.larghezza_piano, t.lunghezza_piano, t.peso
                        FROM odl o
                        JOIN parti p ON o.parte_id = p.id
                        JOIN tools t ON o.tool_id = t.id
                        WHERE o.id IN ({placeholders})
                    """, odl_ids)
                    
                    odl_data = cursor.fetchall()
                    for odl in odl_data:
                        odl_id, status, part_number, tool_name, width, height, peso = odl
                        print(f"  🆔 ODL {odl_id}: {part_number}")
                        print(f"  🔧 Tool: {tool_name}")
                        print(f"  📐 Dimensioni: {width} x {height} mm")
                        print(f"  ⚖️ Peso: {peso} kg")
                        print(f"  🔄 Status: {status}")
                        print("-" * 40)
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ Errore parsing ODL IDs: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore accesso database: {e}")
        return False

def test_api_endpoint():
    """Testa l'endpoint API"""
    print_header("TEST ENDPOINT API")
    
    try:
        # Ottieni lista batch
        response = requests.get("http://localhost:3001/api/v1/batch_nesting", timeout=5)
        
        if response.status_code == 200:
            batches = response.json()
            print(f"✅ Trovati {len(batches)} batch")
            
            if batches:
                batch_id = batches[0]['id']
                print(f"🆔 Test batch ID: {batch_id}")
                
                # Testa endpoint full
                full_response = requests.get(f"http://localhost:3001/api/v1/batch_nesting/{batch_id}/full", timeout=5)
                
                if full_response.status_code == 200:
                    full_data = full_response.json()
                    print("✅ Endpoint /full funziona")
                    
                    # Analizza struttura dati
                    print("\n🔍 STRUTTURA DATI API:")
                    print(f"  🆔 ID: {full_data.get('id')}")
                    print(f"  📝 Nome: {full_data.get('nome')}")
                    print(f"  🏭 Autoclave: {full_data.get('autoclave', {}).get('nome', 'N/A')}")
                    
                    config = full_data.get('configurazione_json')
                    if config:
                        tools = config.get('tool_positions', [])
                        print(f"  🎯 Tool Positions: {len(tools)}")
                        
                        if tools:
                            first_tool = tools[0]
                            print(f"  📊 Primo Tool:")
                            print(f"    ODL ID: {first_tool.get('odl_id')}")
                            print(f"    Posizione: ({first_tool.get('x')}, {first_tool.get('y')})")
                            print(f"    Dimensioni: {first_tool.get('width')} x {first_tool.get('height')}")
                            print(f"    Peso: {first_tool.get('peso')}")
                            print(f"    Ruotato: {first_tool.get('rotated')}")
                    else:
                        print("  ❌ Configurazione JSON mancante")
                        
                else:
                    print(f"❌ Errore endpoint /full: {full_response.status_code}")
                    
        else:
            print(f"❌ Errore API: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore connessione API: {e}")
        print("💡 Assicurati che il backend sia avviato su localhost:3001")

def check_frontend_fetch():
    """Simula il fetch del frontend"""
    print_header("SIMULAZIONE FETCH FRONTEND")
    
    try:
        # Simula esattamente quello che fa il frontend
        response = requests.get("http://localhost:3001/api/v1/batch_nesting", timeout=5)
        
        if response.status_code == 200:
            batches = response.json()
            
            if batches:
                batch_id = batches[0]['id']
                
                # Questo è esattamente quello che fa il frontend
                frontend_url = f"http://localhost:3001/api/v1/batch_nesting/{batch_id}/full"
                print(f"🌐 URL Frontend: {frontend_url}")
                
                frontend_response = requests.get(frontend_url, timeout=5)
                
                if frontend_response.status_code == 200:
                    data = frontend_response.json()
                    
                    print("✅ Frontend fetch simulato con successo")
                    print(f"📊 Dati ricevuti:")
                    print(f"  batchData: presente")
                    print(f"  autoclave: {data.get('autoclave', {}).get('nome', 'mancante')}")
                    print(f"  configurazione_json: {'presente' if data.get('configurazione_json') else 'mancante'}")
                    
                    config = data.get('configurazione_json')
                    if config:
                        tools = config.get('tool_positions', [])
                        print(f"  tool_positions: {len(tools)} elementi")
                        
                        # Verifica validità dati tool
                        for i, tool in enumerate(tools[:3]):
                            print(f"    Tool {i+1}: ODL {tool.get('odl_id')} - "
                                  f"Posizione valida: {tool.get('x') is not None and tool.get('y') is not None}")
                    
                    return data
                else:
                    print(f"❌ Frontend fetch fallito: {frontend_response.status_code}")
                    print(f"Response: {frontend_response.text}")
            else:
                print("❌ Nessun batch trovato")
        else:
            print(f"❌ Errore lista batch: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Errore simulazione frontend: {e}")

def main():
    """Funzione principale"""
    print_header("DEBUG NESTING DATA - ANALISI COMPLETA")
    
    # 1. Controlla database
    db_ok = check_database_data()
    
    # 2. Testa API
    if db_ok:
        test_api_endpoint()
    
    # 3. Simula frontend
    check_frontend_fetch()
    
    print_header("RIEPILOGO")
    print("✅ Analisi completata")
    print("💡 Controlla l'output per identificare problemi nei dati")

if __name__ == "__main__":
    main() 