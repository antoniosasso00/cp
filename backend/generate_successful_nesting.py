#!/usr/bin/env python3
"""
Genera un nesting di successo con tool posizionati per testare il frontend
"""
import sqlite3
import json
from datetime import datetime
import uuid
import requests

def create_successful_nesting():
    """Crea un batch nesting con dati di successo"""
    
    print("🔧 CREAZIONE BATCH NESTING DI SUCCESSO")
    print("=" * 50)
    
    # Connessione database
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    try:
        # Ottieni ODL disponibili per il nesting (primi 2)
        cursor.execute("""
            SELECT o.id, p.part_number, p.descrizione_breve, t.part_number_tool,
                   t.larghezza_piano, t.lunghezza_piano, t.peso
            FROM odl o
            JOIN parti p ON o.parte_id = p.id  
            JOIN tools t ON o.tool_id = t.id
            WHERE o.status = 'Attesa Cura'
            LIMIT 2
        """)
        
        odl_data = cursor.fetchall()
        print(f"📋 ODL disponibili: {len(odl_data)}")
        
        if len(odl_data) < 2:
            print("❌ Servono almeno 2 ODL per il test")
            return
            
        # Dati del batch di successo
        batch_id = str(uuid.uuid4())
        batch_nome = f"Nesting SUCCESS Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Configurazione di layout di successo
        configurazione_json = {
            "canvas_width": 1200.0,
            "canvas_height": 2000.0,
            "scale_factor": 1.0,
            "tool_positions": [
                {
                    "odl_id": odl_data[0][0],
                    "x": 15.0,
                    "y": 15.0,
                    "width": float(odl_data[0][4]),  # larghezza_piano
                    "height": float(odl_data[0][5]), # lunghezza_piano
                    "peso": float(odl_data[0][6]),   # peso
                    "rotated": False,
                    "part_number": odl_data[0][1],
                    "tool_nome": odl_data[0][3]
                },
                {
                    "odl_id": odl_data[1][0],
                    "x": 465.0,  # Posizione accanto al primo
                    "y": 15.0,
                    "width": float(odl_data[1][4]),  # larghezza_piano
                    "height": float(odl_data[1][5]), # lunghezza_piano  
                    "peso": float(odl_data[1][6]),   # peso
                    "rotated": False,
                    "part_number": odl_data[1][1],
                    "tool_nome": odl_data[1][3]
                }
            ],
            "plane_assignments": {
                str(odl_data[0][0]): 1,
                str(odl_data[1][0]): 1
            }
        }
        
        # Calcola statistiche
        total_weight = sum(tool["peso"] for tool in configurazione_json["tool_positions"])
        total_area = sum(tool["width"] * tool["height"] for tool in configurazione_json["tool_positions"])
        autoclave_area = 1200.0 * 2000.0
        efficiency = (total_area / autoclave_area) * 100
        
        # Parametri del nesting
        parametri = {
            "padding_mm": 20.0,
            "min_distance_mm": 15.0,
            "priorita_area": True,
            "accorpamento_odl": False,
            "use_secondary_plane": False,
            "max_weight_per_plane_kg": None
        }
        
        # Inserisci il batch nel database
        cursor.execute("""
            INSERT INTO batch_nesting (
                id, nome, stato, autoclave_id, odl_ids, configurazione_json,
                parametri, numero_nesting, peso_totale_kg, area_totale_utilizzata,
                valvole_totali_utilizzate, note, creato_da_utente, creato_da_ruolo,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            batch_nome,
            'sospeso',
            1,  # autoclave_id
            json.dumps([odl_data[0][0], odl_data[1][0]]),
            json.dumps(configurazione_json),
            json.dumps(parametri),
            1,  # numero_nesting
            total_weight,
            total_area / 10000,  # Converti da mm² a cm²
            2,  # valvole_totali_utilizzate
            f"Batch test con 2 ODL posizionati. Efficienza: {efficiency:.1f}%",
            "test_user",
            "Curing",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
        print(f"✅ Batch creato con successo!")
        print(f"📦 ID: {batch_id}")
        print(f"📛 Nome: {batch_nome}")
        print(f"🎯 Tool posizionati: {len(configurazione_json['tool_positions'])}")
        print(f"⚖️ Peso totale: {total_weight:.1f} kg")
        print(f"📏 Area utilizzata: {total_area/10000:.2f} cm²")
        print(f"📊 Efficienza: {efficiency:.1f}%")
        
        # Test dell'API
        print(f"\n📡 Test API endpoint...")
        try:
            url = f"http://localhost:8000/api/v1/batch_nesting/{batch_id}/full"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                tool_positions = data.get('configurazione_json', {}).get('tool_positions', [])
                print(f"✅ API risponde correttamente")
                print(f"   Tool positions nell'API: {len(tool_positions)}")
                
                # Salva per debug
                with open('debug_successful_batch.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                    
                print(f"\n🌐 URL per il frontend:")
                print(f"http://localhost:3000/dashboard/curing/nesting/result/{batch_id}")
                
            else:
                print(f"❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Errore API: {str(e)}")
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_successful_nesting() 