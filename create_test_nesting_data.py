#!/usr/bin/env python3
"""
Script per creare dati di test per nesting_results nel database CarbonPilot
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random

def create_test_nesting_data():
    """Crea dati di test per nesting_results"""
    print("🚀 Creazione Dati di Test per Nesting Results")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Verifica se esistono già nesting_results
        cursor.execute("SELECT COUNT(*) FROM nesting_results")
        existing_count = cursor.fetchone()[0]
        print(f"📊 Nesting results esistenti: {existing_count}")
        
        # Ottieni autoclavi disponibili
        cursor.execute("SELECT id, nome FROM autoclavi WHERE stato = 'DISPONIBILE'")
        autoclavi = cursor.fetchall()
        print(f"🏭 Autoclavi disponibili: {len(autoclavi)}")
        
        if not autoclavi:
            print("❌ Nessuna autoclave disponibile. Creazione autoclavi di test...")
            # Crea autoclavi di test
            autoclavi_test = [
                ('Autoclave A1', 'DISPONIBILE', 6, 2000, 1500, 300, 500),
                ('Autoclave B2', 'DISPONIBILE', 8, 2500, 1800, 400, 600),
                ('Autoclave C3', 'DISPONIBILE', 4, 1500, 1200, 250, 400)
            ]
            
            for nome, stato, linee, larghezza, profondita, altezza, max_load in autoclavi_test:
                cursor.execute("""
                    INSERT INTO autoclavi (nome, stato, num_linee_vuoto, larghezza_mm, profondita_mm, altezza_mm, max_load_kg)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (nome, stato, linee, larghezza, profondita, altezza, max_load))
            
            conn.commit()
            
            # Ricarica autoclavi
            cursor.execute("SELECT id, nome FROM autoclavi WHERE stato = 'DISPONIBILE'")
            autoclavi = cursor.fetchall()
            print(f"   ✅ Create {len(autoclavi)} autoclavi")
        
        # Ottieni ODL disponibili
        cursor.execute("SELECT id FROM odl WHERE status IN ('Attesa Cura', 'In Coda')")
        odl_ids = [row[0] for row in cursor.fetchall()]
        print(f"📦 ODL disponibili: {len(odl_ids)}")
        
        if len(odl_ids) < 10:
            print("⚠️ Pochi ODL disponibili. Aggiornamento stati ODL...")
            # Aggiorna alcuni ODL per renderli disponibili
            cursor.execute("UPDATE odl SET status = 'Attesa Cura' WHERE status = 'Laminazione' LIMIT 10")
            conn.commit()
            
            # Ricarica ODL
            cursor.execute("SELECT id FROM odl WHERE status IN ('Attesa Cura', 'In Coda')")
            odl_ids = [row[0] for row in cursor.fetchall()]
            print(f"   ✅ ODL aggiornati: {len(odl_ids)}")
        
        # Crea nesting_results di test
        stati_nesting = ['Bozza', 'In sospeso', 'Confermato', 'Caricato', 'Finito']
        
        nesting_creati = 0
        for i in range(15):  # Crea 15 nesting di test
            autoclave = random.choice(autoclavi)
            stato = random.choice(stati_nesting)
            
            # Seleziona ODL casuali per questo nesting
            num_odl = random.randint(2, min(8, len(odl_ids)))
            selected_odl = random.sample(odl_ids, num_odl) if len(odl_ids) >= num_odl else odl_ids[:num_odl]
            
            # Calcola statistiche realistiche
            area_totale = autoclave[0] * 1500 if len(autoclavi) > 0 else 3000000  # Area in cm²
            area_utilizzata = round(random.uniform(area_totale * 0.4, area_totale * 0.9), 2)
            peso_totale = round(random.uniform(10.0, 400.0), 2)
            valvole_utilizzate = random.randint(2, 6)
            valvole_totali = 6
            
            # Efficienza basata sullo stato
            if stato in ['Finito']:
                efficienza_base = random.uniform(0.65, 0.95)
            elif stato in ['Caricato']:
                efficienza_base = random.uniform(0.60, 0.85)
            else:
                efficienza_base = random.uniform(0.50, 0.80)
            
            # Data di creazione negli ultimi 30 giorni
            created_at = datetime.now() - timedelta(days=random.randint(0, 30))
            
            # Motivi esclusione (se ci sono ODL esclusi)
            odl_esclusi = []
            motivi_esclusione = []
            if len(odl_ids) > num_odl and random.random() < 0.3:  # 30% probabilità di avere ODL esclusi
                num_esclusi = random.randint(1, 3)
                remaining_odl = [odl for odl in odl_ids if odl not in selected_odl]
                odl_esclusi = random.sample(remaining_odl, min(num_esclusi, len(remaining_odl)))
                motivi_esclusione = [
                    "Peso eccessivo per l'autoclave",
                    "Ciclo di cura incompatibile",
                    "Dimensioni troppo grandi"
                ][:len(odl_esclusi)]
            
            # Posizioni tool (simulazione layout)
            posizioni_tool = []
            for j, odl_id in enumerate(selected_odl):
                posizioni_tool.append({
                    'odl_id': odl_id,
                    'piano': random.choice([1, 2]),
                    'x': random.randint(50, 1500),
                    'y': random.randint(50, 1200),
                    'width': random.randint(100, 300),
                    'height': random.randint(100, 300)
                })
            
            # Inserisci il nesting_result
            cursor.execute("""
                INSERT INTO nesting_results (
                    autoclave_id, odl_ids, odl_esclusi_ids, motivi_esclusione,
                    stato, area_utilizzata, area_totale, valvole_utilizzate, valvole_totali,
                    peso_totale_kg, area_piano_1, area_piano_2, superficie_piano_2_max,
                    posizioni_tool, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                autoclave[0],  # autoclave_id
                json.dumps(selected_odl),  # odl_ids
                json.dumps(odl_esclusi),  # odl_esclusi_ids
                json.dumps(motivi_esclusione),  # motivi_esclusione
                stato,
                area_utilizzata,
                area_totale,
                valvole_utilizzate,
                valvole_totali,
                peso_totale,
                area_utilizzata * 0.6,  # area_piano_1
                area_utilizzata * 0.4,  # area_piano_2
                area_totale * 0.5,  # superficie_piano_2_max
                json.dumps(posizioni_tool),  # posizioni_tool
                created_at.isoformat(),
                created_at.isoformat()
            ))
            
            nesting_id = cursor.lastrowid
            
            # Crea le relazioni nesting_result_odl
            for odl_id in selected_odl:
                cursor.execute("""
                    INSERT INTO nesting_result_odl (nesting_result_id, odl_id)
                    VALUES (?, ?)
                """, (nesting_id, odl_id))
            
            nesting_creati += 1
            print(f"   ✅ Creato nesting {nesting_id} con {len(selected_odl)} ODL (stato: {stato})")
        
        conn.commit()
        print(f"\n🎉 Creati {nesting_creati} nesting results di test!")
        
        # Verifica finale
        cursor.execute("SELECT COUNT(*) FROM nesting_results")
        total_count = cursor.fetchone()[0]
        print(f"📊 Totale nesting results nel database: {total_count}")
        
        # Mostra distribuzione per stato
        cursor.execute("SELECT stato, COUNT(*) FROM nesting_results GROUP BY stato")
        distribuzione = cursor.fetchall()
        print("\n📈 Distribuzione per stato:")
        for stato, count in distribuzione:
            print(f"   {stato}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore durante la creazione dei dati: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def verify_data():
    """Verifica i dati creati"""
    print("\n🔍 Verifica Dati Creati")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Verifica nesting_results con join
        cursor.execute("""
            SELECT nr.id, nr.stato, a.nome as autoclave_nome, nr.peso_totale_kg, 
                   nr.area_utilizzata, nr.area_totale, nr.created_at
            FROM nesting_results nr
            LEFT JOIN autoclavi a ON nr.autoclave_id = a.id
            ORDER BY nr.created_at DESC
            LIMIT 5
        """)
        
        recent_nestings = cursor.fetchall()
        print("📊 Ultimi 5 nesting results:")
        for nesting in recent_nestings:
            efficienza = (nesting[4] / nesting[5] * 100) if nesting[5] > 0 else 0
            print(f"   ID: {nesting[0]} | Stato: {nesting[1]} | Autoclave: {nesting[2]} | Peso: {nesting[3]}kg | Efficienza: {efficienza:.1f}%")
        
        # Verifica relazioni ODL
        cursor.execute("""
            SELECT nr.id, COUNT(nro.odl_id) as odl_count
            FROM nesting_results nr
            LEFT JOIN nesting_result_odl nro ON nr.id = nro.nesting_result_id
            GROUP BY nr.id
            ORDER BY nr.id DESC
            LIMIT 5
        """)
        
        nesting_with_odl = cursor.fetchall()
        print("\n🔗 Nesting con ODL associati:")
        for item in nesting_with_odl:
            print(f"   Nesting {item[0]}: {item[1]} ODL")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")

if __name__ == "__main__":
    create_test_nesting_data()
    verify_data() 