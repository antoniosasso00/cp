#!/usr/bin/env python3
"""
Script semplificato per testare il sistema di efficienza dei batch nesting.
Crea direttamente un batch nel database SQLite con efficienza 55%.
"""

import sqlite3
import uuid
from datetime import datetime

def create_test_efficiency_batch():
    """Crea un batch con efficienza del 55% direttamente nel database"""
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        print("🧪 Creazione batch di test per efficienza...")
        
        # Verifica se esiste un'autoclave
        cursor.execute("SELECT id, nome, lunghezza, larghezza_piano, num_linee_vuoto FROM autoclavi LIMIT 1")
        autoclave = cursor.fetchone()
        
        if not autoclave:
            print("📦 Creazione autoclave di test...")
            autoclave_id = 999
            cursor.execute("""
                INSERT INTO autoclavi (
                    id, nome, codice, lunghezza, larghezza_piano, 
                    num_linee_vuoto, max_load_kg, stato, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                autoclave_id,
                "Autoclave Test Efficienza",
                "AUTO-TEST-EFF",
                1000.0,  # 1000mm lunghezza
                800.0,   # 800mm larghezza
                10,      # 10 linee vuoto
                500.0,   # 500kg max
                "DISPONIBILE",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            autoclave = (autoclave_id, "Autoclave Test Efficienza", 1000.0, 800.0, 10)
        
        autoclave_id, nome, lunghezza, larghezza_piano, num_linee_vuoto = autoclave
        
        # Calcoli per efficienza 55%
        area_totale_autoclave = lunghezza * larghezza_piano  # 800,000 mm²
        area_target_mm2 = area_totale_autoclave * 0.55      # 440,000 mm²
        area_target_cm2 = area_target_mm2 / 100             # 4,400 cm²
        valvole_target = int(num_linee_vuoto * 0.5)         # 5 valvole (50%)
        
        # Formula efficienza: 0.7 * area_pct + 0.3 * vacuum_util_pct
        # 0.7 * 55 + 0.3 * 50 = 38.5 + 15 = 53.5% (badge ROSSO)
        
        print(f"🎯 Target: Area {area_target_cm2:.0f} cm², Valvole {valvole_target}")
        print(f"🎯 Efficienza attesa: ~53.5% (BADGE ROSSO)")
        
        # Crea il batch nesting
        batch_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO batch_nesting (
                id, nome, stato, autoclave_id, odl_ids, 
                area_totale_utilizzata, valvole_totali_utilizzate, peso_totale_kg,
                numero_nesting, note, efficiency, 
                creato_da_utente, creato_da_ruolo, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            "Batch Test Efficienza 55%",
            "sospeso",
            autoclave_id,
            '[1,2,3]',  # ODL IDs fittizi
            area_target_cm2,
            valvole_target,
            150,  # peso kg
            1,    # numero nesting
            "Batch di test per sistema di efficienza - efficienza target 55%",
            53.5, # efficienza pre-calcolata
            "test_system",
            "ADMIN",
            now,
            now
        ))
        
        conn.commit()
        
        # Verifica il risultato
        cursor.execute("""
            SELECT b.id, b.efficiency, b.area_totale_utilizzata, b.valvole_totali_utilizzate,
                   a.lunghezza, a.larghezza_piano, a.num_linee_vuoto
            FROM batch_nesting b
            JOIN autoclavi a ON b.autoclave_id = a.id
            WHERE b.id = ?
        """, (batch_id,))
        
        result = cursor.fetchone()
        if result:
            bid, efficiency, area_util, valvole_util, lung, larg, linee_vuoto = result
            
            # Calcola le metriche
            area_totale = lung * larg
            area_pct = (area_util * 100) / (area_totale / 100)  # Conversione cm² vs mm²
            vacuum_pct = (valvole_util / linee_vuoto) * 100
            efficiency_calc = (0.7 * area_pct) + (0.3 * vacuum_pct)
            
            print(f"✅ Batch creato con successo!")
            print(f"   ID: {bid}")
            print(f"   Area %: {area_pct:.1f}%")
            print(f"   Vacuum %: {vacuum_pct:.1f}%") 
            print(f"   Efficienza: {efficiency_calc:.1f}%")
            
            # Determina livello
            if efficiency_calc >= 80:
                level = "GREEN"
                color = "bg-green-500"
            elif efficiency_calc >= 60:
                level = "YELLOW" 
                color = "bg-amber-500"
            else:
                level = "RED"
                color = "bg-red-500"
                
            print(f"   Livello: {level}")
            print(f"   Classe CSS: {color}")
            
            if level == "RED":
                print("🔴 Badge ROSSO confermato - il toast warning dovrebbe apparire!")
            
            return bid
        
    except Exception as e:
        print(f"❌ Errore nella creazione del batch: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 SEED SCRIPT - Test Efficienza Batch Nesting")
    print("=" * 50)
    
    batch_id = create_test_efficiency_batch()
    
    print("\n📋 ISTRUZIONI PER IL TEST:")
    print("1. Avvia il backend: cd backend && uvicorn main:app --reload --port 8000")
    print("2. Avvia il frontend: cd frontend && npm run dev")
    print("3. Vai alla pagina nesting preview: http://localhost:3000/dashboard/curing/nesting/preview")
    print("4. Genera una preview con parametri che diano efficienza <60%")
    print("5. Verifica che appaia il warning toast rosso")
    print(f"6. ID Batch di test creato: {batch_id}")
    print("=" * 50) 