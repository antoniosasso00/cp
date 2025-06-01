#!/usr/bin/env python3
"""
Debug dei problemi frontend:
1. ODL inclusi ma non posizionati
2. Canvas non visibile  
3. Nesting list non funzionante
"""

import sys
sys.path.append('.')

import requests
import json

def debug_api_data():
    """Debug dei dati API per il frontend"""
    
    print("🔍 DEBUG PROBLEMI FRONTEND")
    print("=" * 50)
    
    # 1. Test lista batch nesting
    print("\n📋 1. LISTA BATCH NESTING:")
    try:
        response = requests.get('http://localhost:8000/api/v1/batch_nesting/')
        if response.status_code == 200:
            batches = response.json()
            print(f"   ✅ {len(batches)} batch trovati")
            
            if batches:
                latest_batch = batches[0]  # Prendi il più recente
                batch_id = latest_batch['id']
                print(f"   📊 Ultimo batch: {batch_id}")
                print(f"   📊 Nome: {latest_batch.get('nome')}")
                print(f"   📊 Stato: {latest_batch.get('stato')}")
                print(f"   📊 ODL IDs: {latest_batch.get('odl_ids')}")
                
                # 2. Test dettaglio batch completo
                print(f"\n🔍 2. DETTAGLIO BATCH {batch_id}:")
                detail_response = requests.get(f'http://localhost:8000/api/v1/batch_nesting/{batch_id}/full')
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print("   ✅ Dettagli caricati correttamente")
                    
                    # Verifica configurazione_json
                    config = detail_data.get('configurazione_json')
                    print(f"   📊 configurazione_json presente: {bool(config)}")
                    
                    if config:
                        # Analizza struttura configurazione
                        print(f"\n📊 3. ANALISI CONFIGURAZIONE_JSON:")
                        print(f"   Canvas width: {config.get('canvas_width')}")
                        print(f"   Canvas height: {config.get('canvas_height')}")
                        
                        tool_positions = config.get('tool_positions', [])
                        print(f"   Tool positions: {len(tool_positions)}")
                        
                        if tool_positions:
                            print(f"\n   🔧 POSIZIONI TOOL:")
                            for i, pos in enumerate(tool_positions):
                                print(f"     • Tool {i+1}: ODL {pos.get('odl_id')}")
                                print(f"       - Posizione: ({pos.get('x')}, {pos.get('y')})")
                                print(f"       - Dimensioni: {pos.get('width')}x{pos.get('height')}mm")
                                print(f"       - Peso: {pos.get('peso')}kg")
                                print(f"       - Ruotato: {pos.get('rotated', False)}")
                                print()
                            
                            # Verifica se le posizioni sono valide
                            canvas_width = config.get('canvas_width', 0)
                            canvas_height = config.get('canvas_height', 0)
                            
                            print(f"   🔍 VALIDAZIONE POSIZIONI:")
                            valid_positions = 0
                            for pos in tool_positions:
                                x = pos.get('x', 0)
                                y = pos.get('y', 0) 
                                width = pos.get('width', 0)
                                height = pos.get('height', 0)
                                
                                if x >= 0 and y >= 0 and (x + width) <= canvas_width and (y + height) <= canvas_height:
                                    valid_positions += 1
                                    print(f"     ✅ ODL {pos.get('odl_id')}: posizione valida")
                                else:
                                    print(f"     ❌ ODL {pos.get('odl_id')}: posizione NON valida")
                                    print(f"        Bounds: ({x}, {y}) + ({width}x{height}) vs canvas {canvas_width}x{canvas_height}")
                            
                            print(f"   📊 Posizioni valide: {valid_positions}/{len(tool_positions)}")
                        else:
                            print("   ❌ NESSUNA POSIZIONE TOOL TROVATA!")
                            print("   🔧 Problema: configurazione_json ha tool_positions vuoto")
                            
                        # Verifica plane_assignments
                        plane_assignments = config.get('plane_assignments', {})
                        print(f"   📊 Plane assignments: {len(plane_assignments)}")
                        if plane_assignments:
                            print(f"     {dict(list(plane_assignments.items())[:3])}...")
                            
                    else:
                        print("   ❌ CONFIGURAZIONE_JSON MANCANTE!")
                        print("   🔧 Problema: il batch non ha la configurazione per il canvas")
                    
                    # Verifica autoclave info
                    autoclave = detail_data.get('autoclave')
                    print(f"\n🏭 4. INFO AUTOCLAVE:")
                    if autoclave:
                        print(f"   ✅ Autoclave: {autoclave.get('nome')}")
                        print(f"   📊 Dimensioni: {autoclave.get('larghezza_piano')}x{autoclave.get('lunghezza')}mm")
                        print(f"   📊 ID: {autoclave.get('id')}")
                        print(f"   📊 Codice: {autoclave.get('codice')}")
                    else:
                        print("   ❌ Info autoclave mancanti!")
                        
                else:
                    print(f"   ❌ Errore nel caricamento dettagli: {detail_response.status_code}")
                    print(f"   Response: {detail_response.text[:200]}")
                    
            else:
                print("   ⚠️ Nessun batch presente")
                print("   🔧 Genera prima un nesting per avere dati da visualizzare")
                
        else:
            print(f"   ❌ Errore API lista batch: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Errore: {str(e)}")

def check_frontend_compatibility():
    """Verifica compatibilità frontend"""
    
    print(f"\n🌐 5. COMPATIBILITÀ FRONTEND:")
    
    # Test struttura dati per il canvas
    print("   📊 Struttura dati richiesta dal canvas:")
    print("     • configurazione_json.canvas_width (number)")
    print("     • configurazione_json.canvas_height (number)")
    print("     • configurazione_json.tool_positions (array)")
    print("       - odl_id, x, y, width, height, peso, rotated")
    print("     • autoclave.nome, larghezza_piano, lunghezza")
    
    # Test endpoint necessari per le pagine
    endpoints_required = [
        '/api/v1/batch_nesting/',
        '/api/v1/batch_nesting/{id}/full',
        '/api/v1/odl/',
        '/api/v1/autoclavi/',
        '/api/v1/nesting/genera'
    ]
    
    print(f"\n   📊 Endpoint richiesti dal frontend:")
    for endpoint in endpoints_required:
        print(f"     • {endpoint}")

def diagnose_canvas_issues():
    """Diagnosi problemi canvas"""
    
    print(f"\n🖼️ 6. DIAGNOSI PROBLEMI CANVAS:")
    print("   🔍 Possibili cause canvas non visibile:")
    print("     • Dati tool_positions vuoti o malformati")
    print("     • Errori nell'import di react-konva")
    print("     • Problemi di dimensioni/scala del canvas")
    print("     • Errori SSR/client-side rendering")
    
    print(f"\n   🔧 Soluzioni suggerite:")
    print("     • Verificare che tool_positions contenga coordinate valide")
    print("     • Controllare console browser per errori JavaScript")
    print("     • Verificare import dinamico di react-konva")
    print("     • Testare con dati mock per isolare il problema")

if __name__ == "__main__":
    debug_api_data()
    check_frontend_compatibility()
    diagnose_canvas_issues()
    
    print(f"\n" + "=" * 50)
    print("🏁 DEBUG COMPLETATO")
    print("🔧 Controlla i risultati sopra per identificare i problemi") 