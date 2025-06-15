#!/usr/bin/env python3
"""
🔍 CarbonPilot - Diagnosi Batch 2L
Verifica dettagliata del contenuto dei batch per identificare problemi di visualizzazione
"""

import requests
import json
from datetime import datetime

def check_batch_details():
    """Verifica dettagliata dei batch 2L recenti"""
    print("🔍 DIAGNOSI BATCH 2L - Verifica Contenuto Dettagliato")
    print("=" * 60)
    
    # 1. Recupera lista batch recenti
    print("📊 Recupero batch 2L recenti...")
    response = requests.get('http://localhost:8000/api/batch_nesting/')
    
    if response.status_code != 200:
        print(f"❌ Errore API list-batches: {response.status_code}")
        return
    
    batches = response.json()
    if not batches:
        print("❌ Nessun batch 2L trovato")
        return
    
    print(f"✅ Trovati {len(batches)} batch 2L")
    
    # 2. Filtra solo batch 2L e analizza
    batch_2l = [b for b in batches if '2L' in b.get('nome', '')]
    print(f"✅ Batch 2L trovati: {len(batch_2l)}")
    
    for i, batch in enumerate(batch_2l[:3]):  # Primi 3 batch 2L
        batch_id = batch['id']
        autoclave_nome = batch.get('nome', 'N/A')
        peso = batch.get('peso_totale_kg', 0)
        
        print(f"\n🎯 BATCH #{i+1}: ID {batch_id}")
        print(f"   Nome: {autoclave_nome}")
        print(f"   Peso: {peso:.1f} kg")
        print(f"   Stato: {batch.get('stato', 'N/A')}")
        print(f"   Creato: {batch.get('created_at', 'N/A')}")
        
        # Recupera dettagli completi del batch
        detail_response = requests.get(f'http://localhost:8000/api/batch_nesting/{batch_id}')
        
        if detail_response.status_code != 200:
            print(f"   ❌ Errore dettagli batch: {detail_response.status_code}")
            continue
        
        try:
            batch_details = detail_response.json()
            
            # Verifica struttura configurazione
            config = batch_details.get('configurazione_json', {})
            
            print(f"   📦 Configurazione presente: {'✅' if config else '❌'}")
            
            if config:
                # Verifica campi critici
                positioned_tools = config.get('positioned_tools', [])
                cavalletti = config.get('cavalletti_positions', [])
                metrics = config.get('metrics', {})
                autoclave_info = config.get('autoclave_info', {})
                
                print(f"   🔧 Tool posizionati: {len(positioned_tools)}")
                print(f"   🎯 Cavalletti: {len(cavalletti)}")
                print(f"   📊 Metriche: {'✅' if metrics else '❌'}")
                print(f"   🏭 Info autoclave: {'✅' if autoclave_info else '❌'}")
                
                # Analisi tool posizionati
                if positioned_tools:
                    level_0_count = len([t for t in positioned_tools if t.get('level', 0) == 0])
                    level_1_count = len([t for t in positioned_tools if t.get('level', 0) == 1])
                    print(f"      Livello 0: {level_0_count} tool")
                    print(f"      Livello 1: {level_1_count} tool")
                    
                    # Verifica struttura primo tool
                    first_tool = positioned_tools[0]
                    required_fields = ['odl_id', 'x', 'y', 'width', 'height', 'level']
                    missing_fields = [f for f in required_fields if f not in first_tool]
                    
                    if missing_fields:
                        print(f"      ⚠️ Campi mancanti nel tool: {missing_fields}")
                    else:
                        print(f"      ✅ Struttura tool corretta")
                        print(f"         Esempio: ODL {first_tool['odl_id']} a ({first_tool['x']:.0f},{first_tool['y']:.0f})")
                
                # Analisi cavalletti
                if cavalletti:
                    cavalletti_per_tool = {}
                    for cav in cavalletti:
                        tool_id = cav.get('tool_odl_id', 'N/A')
                        if tool_id not in cavalletti_per_tool:
                            cavalletti_per_tool[tool_id] = 0
                        cavalletti_per_tool[tool_id] += 1
                    
                    print(f"      🎯 Cavalletti per tool:")
                    for tool_id, count in cavalletti_per_tool.items():
                        print(f"         ODL {tool_id}: {count} cavalletti")
                
                # Verifica metriche
                if metrics:
                    print(f"      📊 Metriche chiave:")
                    print(f"         Area: {metrics.get('area_utilization_pct', 0):.1f}%")
                    print(f"         Efficienza: {metrics.get('efficiency_score', 0):.1f}%")
                    print(f"         Algoritmo: {metrics.get('algorithm_status', 'N/A')}")
                    print(f"         Timeout: {metrics.get('timeout_used_seconds', 0):.1f}s")
                
                # Verifica presenza campi frontend critici
                frontend_fields = ['success', 'message', 'excluded_odls', 'excluded_reasons']
                missing_frontend = [f for f in frontend_fields if f not in config]
                
                if missing_frontend:
                    print(f"      ⚠️ Campi frontend mancanti: {missing_frontend}")
                else:
                    print(f"      ✅ Campi frontend completi")
                    print(f"         Success: {config.get('success', False)}")
                    print(f"         Message: {config.get('message', 'N/A')[:50]}...")
                
            else:
                print(f"   ❌ PROBLEMA: Configurazione vuota o mancante!")
                print(f"      Raw response keys: {list(batch_details.keys())}")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ Errore parsing JSON: {str(e)}")
        except Exception as e:
            print(f"   ❌ Errore generico: {str(e)}")
    
    print(f"\n🎯 DIAGNOSI COMPLETATA")
    print("=" * 60)

if __name__ == "__main__":
    check_batch_details() 