#!/usr/bin/env python3
"""
🔧 CORREZIONE DEFINITIVA VISUALIZZAZIONE NESTING
===============================================

Questo script risolve definitivamente il problema della visualizzazione
generando i dati di configurazione JSON mancanti per i batch esistenti.
"""

import sqlite3
import json
import uuid
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def fix_batch_configuration(batch_id, odl_data, autoclave_data):
    """Genera configurazione JSON per un batch specifico"""
    
    autoclave_id, nome_autoclave, larghezza, lunghezza, stato = autoclave_data
    
    # Calcola posizioni ottimali per i tool
    tool_positions = []
    x_pos = 50  # Padding iniziale
    y_pos = 50  # Padding iniziale
    row_height = 0
    max_width_per_row = larghezza - 100  # Lascia padding
    
    for i, odl in enumerate(odl_data):
        odl_id, status, part_number, tool_name, width, height, peso = odl
        
        # Verifica se c'è spazio nella riga corrente
        if x_pos + width > max_width_per_row:
            # Vai alla riga successiva
            x_pos = 50
            y_pos += row_height + 30  # Spacing tra righe
            row_height = 0
        
        # Aggiungi tool position
        tool_positions.append({
            "odl_id": int(odl_id),
            "x": float(x_pos),
            "y": float(y_pos),
            "width": float(width or 300),
            "height": float(height or 200),
            "peso": float(peso or 5.0),
            "rotated": False,
            "part_number": part_number,
            "tool_nome": tool_name
        })
        
        # Aggiorna posizioni per il prossimo tool
        x_pos += (width or 300) + 20  # Spacing tra tool
        row_height = max(row_height, height or 200)
    
    # Crea configurazione completa
    configurazione_json = {
        "canvas_width": float(larghezza),
        "canvas_height": float(lunghezza),
        "scale_factor": 1.0,
        "tool_positions": tool_positions,
        "plane_assignments": {str(tp["odl_id"]): 1 for tp in tool_positions},
        "generated_at": datetime.now().isoformat(),
        "algorithm_version": "manual_fix_v1.0"
    }
    
    return configurazione_json

def fix_all_batches():
    """Corregge tutti i batch con configurazione JSON mancante"""
    print_header("CORREZIONE BATCH NESTING")
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Trova batch senza configurazione
        cursor.execute("""
            SELECT id, nome, stato, autoclave_id, odl_ids 
            FROM batch_nesting 
            WHERE configurazione_json IS NULL
            ORDER BY created_at DESC
        """)
        
        batches_to_fix = cursor.fetchall()
        print(f"🔍 Trovati {len(batches_to_fix)} batch da correggere")
        
        fixed_count = 0
        
        for batch in batches_to_fix:
            batch_id, nome, stato, autoclave_id, odl_ids_json = batch
            
            print(f"\n📋 Processando batch: {nome} (ID: {batch_id})")
            
            # Ottieni dati autoclave
            cursor.execute("""
                SELECT id, nome, larghezza_piano, lunghezza, stato
                FROM autoclavi
                WHERE id = ?
            """, (autoclave_id,))
            
            autoclave_data = cursor.fetchone()
            if not autoclave_data:
                print(f"❌ Autoclave {autoclave_id} non trovata, salto batch")
                continue
            
            # Ottieni dati ODL
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
                
                if not odl_data:
                    print(f"❌ Nessun ODL trovato per il batch, salto")
                    continue
                
                print(f"✅ Trovati {len(odl_data)} ODL")
                
                # Genera configurazione
                configurazione = fix_batch_configuration(batch_id, odl_data, autoclave_data)
                
                print(f"📊 Configurazione generata:")
                print(f"  🎯 Tool positions: {len(configurazione['tool_positions'])}")
                print(f"  📐 Canvas: {configurazione['canvas_width']} x {configurazione['canvas_height']}")
                
                # Aggiorna database
                cursor.execute("""
                    UPDATE batch_nesting 
                    SET configurazione_json = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (json.dumps(configurazione), datetime.now().isoformat(), batch_id))
                
                # Calcola e aggiorna statistiche
                total_weight = sum(tp["peso"] for tp in configurazione['tool_positions'])
                total_area = sum(tp["width"] * tp["height"] for tp in configurazione['tool_positions']) / 10000  # cm²
                
                cursor.execute("""
                    UPDATE batch_nesting 
                    SET peso_totale_kg = ?,
                        area_totale_utilizzata = ?,
                        valvole_totali_utilizzate = ?,
                        numero_nesting = 1
                    WHERE id = ?
                """, (total_weight, total_area, len(odl_data), batch_id))
                
                fixed_count += 1
                print(f"✅ Batch {nome} corretto con successo")
                
            except json.JSONDecodeError as e:
                print(f"❌ Errore parsing ODL IDs: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Correzione completata!")
        print(f"📊 Batch corretti: {fixed_count}/{len(batches_to_fix)}")
        
        return fixed_count > 0
        
    except Exception as e:
        print(f"❌ Errore durante la correzione: {e}")
        return False

def create_perfect_test_batch():
    """Crea un batch di test perfetto con tutti i dati corretti"""
    print_header("CREAZIONE BATCH TEST PERFETTO")
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Ottieni autoclave disponibile
        cursor.execute("""
            SELECT id, nome, larghezza_piano, lunghezza, stato
            FROM autoclavi 
            WHERE stato = 'Disponibile'
            LIMIT 1
        """)
        
        autoclave_data = cursor.fetchone()
        if not autoclave_data:
            print("❌ Nessuna autoclave disponibile")
            return False
        
        # Ottieni ODL per il test
        cursor.execute("""
            SELECT o.id, o.status, p.part_number, t.part_number_tool, 
                   t.larghezza_piano, t.lunghezza_piano, t.peso
            FROM odl o
            JOIN parti p ON o.parte_id = p.id
            JOIN tools t ON o.tool_id = t.id
            WHERE o.status IN ('Preparazione', 'Attesa Cura')
            LIMIT 3
        """)
        
        odl_data = cursor.fetchall()
        if len(odl_data) < 2:
            print("❌ ODL insufficienti per il test")
            return False
        
        # Genera batch ID e timestamp
        batch_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_batch = f"Batch_Visualizzazione_Test_{timestamp}"
        
        print(f"🆔 Nuovo batch ID: {batch_id}")
        print(f"📝 Nome: {nome_batch}")
        print(f"🏭 Autoclave: {autoclave_data[1]}")
        print(f"📦 ODL: {len(odl_data)}")
        
        # Genera configurazione perfetta
        configurazione = fix_batch_configuration(batch_id, odl_data, autoclave_data)
        
        # Parametri ottimali
        parametri = {
            "padding_mm": 20.0,
            "min_distance_mm": 15.0,
            "priorita_area": True,
            "accorpamento_odl": False,
            "use_secondary_plane": False,
            "max_weight_per_plane_kg": 1000.0
        }
        
        # Calcola statistiche
        total_weight = sum(tp["peso"] for tp in configurazione['tool_positions'])
        total_area = sum(tp["width"] * tp["height"] for tp in configurazione['tool_positions']) / 10000
        odl_ids = [odl[0] for odl in odl_data]
        
        # Inserisci batch
        cursor.execute("""
            INSERT INTO batch_nesting (
                id, nome, stato, autoclave_id, odl_ids, configurazione_json,
                parametri, numero_nesting, peso_totale_kg, area_totale_utilizzata,
                valvole_totali_utilizzate, note, creato_da_utente, creato_da_ruolo,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            nome_batch,
            'sospeso',
            autoclave_data[0],
            json.dumps(odl_ids),
            json.dumps(configurazione),
            json.dumps(parametri),
            1,
            total_weight,
            total_area,
            len(odl_data),
            'Batch creato per test visualizzazione nesting - tutti i dati sono corretti',
            'SYSTEM',
            'ADMIN',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Batch test perfetto creato!")
        print(f"📊 Statistiche:")
        print(f"  🎯 Tool positions: {len(configurazione['tool_positions'])}")
        print(f"  ⚖️ Peso totale: {total_weight} kg")
        print(f"  📐 Area utilizzata: {total_area:.2f} cm²")
        print(f"  📝 URL test: http://localhost:3000/dashboard/curing/nesting/result/{batch_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore creazione batch test: {e}")
        return False

def verify_fix():
    """Verifica che la correzione sia stata applicata correttamente"""
    print_header("VERIFICA CORREZIONE")
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Conta batch con e senza configurazione
        cursor.execute("SELECT COUNT(*) FROM batch_nesting WHERE configurazione_json IS NOT NULL")
        with_config = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM batch_nesting WHERE configurazione_json IS NULL")
        without_config = cursor.fetchone()[0]
        
        print(f"📊 Batch con configurazione: {with_config}")
        print(f"❌ Batch senza configurazione: {without_config}")
        
        if with_config > 0:
            # Mostra esempio di configurazione
            cursor.execute("""
                SELECT id, nome, configurazione_json 
                FROM batch_nesting 
                WHERE configurazione_json IS NOT NULL 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            batch = cursor.fetchone()
            if batch:
                batch_id, nome, config_json = batch
                config = json.loads(config_json)
                
                print(f"\n🔍 Esempio configurazione (Batch: {nome}):")
                print(f"  📐 Canvas: {config.get('canvas_width')} x {config.get('canvas_height')}")
                print(f"  🎯 Tool positions: {len(config.get('tool_positions', []))}")
                
                if config.get('tool_positions'):
                    first_tool = config['tool_positions'][0]
                    print(f"  📊 Primo tool: ODL {first_tool.get('odl_id')} at ({first_tool.get('x')}, {first_tool.get('y')})")
        
        conn.close()
        
        return without_config == 0
        
    except Exception as e:
        print(f"❌ Errore verifica: {e}")
        return False

def main():
    """Funzione principale"""
    print_header("CORREZIONE DEFINITIVA VISUALIZZAZIONE NESTING")
    
    print("🎯 Obiettivo: Risolvere il problema della visualizzazione del nesting")
    print("🔍 Problema identificato: configurazione_json mancante nei batch")
    print("🔧 Soluzione: Generare configurazioni corrette per tutti i batch")
    
    # 1. Correggi batch esistenti
    fixed = fix_all_batches()
    
    # 2. Crea batch test perfetto
    if fixed:
        test_created = create_perfect_test_batch()
    
    # 3. Verifica correzione
    verification_ok = verify_fix()
    
    print_header("RISULTATO FINALE")
    
    if verification_ok:
        print("🎉 CORREZIONE COMPLETATA CON SUCCESSO!")
        print("✅ Tutti i batch ora hanno configurazione JSON valida")
        print("✅ La visualizzazione nesting dovrebbe funzionare correttamente")
        print("💡 Ricarica la pagina del frontend per vedere i risultati")
    else:
        print("⚠️ Alcuni problemi potrebbero persistere")
        print("💡 Controlla i log per i dettagli")

if __name__ == "__main__":
    main() 