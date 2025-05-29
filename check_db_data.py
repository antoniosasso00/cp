#!/usr/bin/env python3
"""
Script per verificare e creare dati di test nel database CarbonPilot
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
import random

def check_database():
    """Verifica i dati presenti nel database"""
    print("🔍 Verifica Database CarbonPilot")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Verifica tabelle esistenti
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Tabelle trovate: {[t[0] for t in tables]}")
        
        # Verifica ODL
        cursor.execute("SELECT COUNT(*) FROM odl")
        odl_count = cursor.fetchone()[0]
        print(f"📦 ODL totali: {odl_count}")
        
        if odl_count > 0:
            cursor.execute("SELECT status, COUNT(*) FROM odl GROUP BY status")
            odl_by_status = cursor.fetchall()
            print(f"   Per stato: {dict(odl_by_status)}")
        
        # Verifica Autoclavi
        cursor.execute("SELECT COUNT(*) FROM autoclavi")
        autoclave_count = cursor.fetchone()[0]
        print(f"🏭 Autoclavi totali: {autoclave_count}")
        
        if autoclave_count > 0:
            cursor.execute("SELECT stato, COUNT(*) FROM autoclavi GROUP BY stato")
            autoclave_by_status = cursor.fetchall()
            print(f"   Per stato: {dict(autoclave_by_status)}")
        
        # Verifica Nesting
        cursor.execute("SELECT COUNT(*) FROM nesting")
        nesting_count = cursor.fetchone()[0]
        print(f"🎯 Nesting totali: {nesting_count}")
        
        if nesting_count > 0:
            cursor.execute("SELECT stato, COUNT(*) FROM nesting GROUP BY stato")
            nesting_by_status = cursor.fetchall()
            print(f"   Per stato: {dict(nesting_by_status)}")
            
            # Mostra alcuni nesting di esempio
            cursor.execute("""
                SELECT id, stato, autoclave_nome, peso_totale, efficienza, created_at 
                FROM nesting 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            recent_nestings = cursor.fetchall()
            print("\n📊 Ultimi 5 nesting:")
            for nesting in recent_nestings:
                print(f"   ID: {nesting[0][:8]}... | Stato: {nesting[1]} | Autoclave: {nesting[2]} | Peso: {nesting[3]} kg | Efficienza: {nesting[4]}%")
        
        conn.close()
        return nesting_count, odl_count, autoclave_count
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
        return 0, 0, 0

def create_test_data():
    """Crea dati di test se il database è vuoto"""
    print("\n🚀 Creazione Dati di Test")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Crea autoclavi di test se non esistono
        cursor.execute("SELECT COUNT(*) FROM autoclavi")
        if cursor.fetchone()[0] == 0:
            print("🏭 Creazione autoclavi di test...")
            autoclavi_test = [
                ('Autoclave A1', 'DISPONIBILE', 6, 2000, 1500, 300),
                ('Autoclave B2', 'DISPONIBILE', 8, 2500, 1800, 400),
                ('Autoclave C3', 'MANUTENZIONE', 4, 1500, 1200, 250)
            ]
            
            for nome, stato, linee, larghezza, profondita, altezza in autoclavi_test:
                autoclave_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO autoclavi (id, nome, stato, num_linee_vuoto, larghezza_mm, profondita_mm, altezza_mm)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (autoclave_id, nome, stato, linee, larghezza, profondita, altezza))
            
            print(f"   ✅ Create {len(autoclavi_test)} autoclavi")
        
        # Crea ODL di test se non esistono
        cursor.execute("SELECT COUNT(*) FROM odl")
        if cursor.fetchone()[0] == 0:
            print("📦 Creazione ODL di test...")
            
            tool_names = ['Tool_A', 'Tool_B', 'Tool_C', 'Tool_D', 'Tool_E']
            parte_codes = ['P001', 'P002', 'P003', 'P004', 'P005']
            
            for i in range(20):  # Crea 20 ODL di test
                odl_id = str(uuid.uuid4())
                tool_name = random.choice(tool_names)
                parte_code = random.choice(parte_codes)
                peso = round(random.uniform(0.5, 5.0), 2)
                larghezza = random.randint(50, 200)
                profondita = random.randint(50, 200)
                altezza = random.randint(10, 50)
                
                cursor.execute("""
                    INSERT INTO odl (id, tool_nome, parte_codice, peso_kg, larghezza_mm, profondita_mm, altezza_mm, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'DISPONIBILE')
                """, (odl_id, tool_name, parte_code, peso, larghezza, profondita, altezza))
            
            print(f"   ✅ Creati 20 ODL di test")
        
        # Crea nesting di test se non esistono
        cursor.execute("SELECT COUNT(*) FROM nesting")
        if cursor.fetchone()[0] == 0:
            print("🎯 Creazione nesting di test...")
            
            # Ottieni autoclavi disponibili
            cursor.execute("SELECT id, nome FROM autoclavi WHERE stato = 'DISPONIBILE'")
            autoclavi = cursor.fetchall()
            
            # Ottieni ODL disponibili
            cursor.execute("SELECT id FROM odl WHERE status = 'DISPONIBILE'")
            odl_ids = [row[0] for row in cursor.fetchall()]
            
            if autoclavi and odl_ids:
                stati_nesting = ['bozza', 'confermato', 'sospeso', 'cura', 'finito', 'completato']
                
                for i in range(10):  # Crea 10 nesting di test
                    nesting_id = str(uuid.uuid4())
                    autoclave = random.choice(autoclavi)
                    stato = random.choice(stati_nesting)
                    
                    # Seleziona alcuni ODL casuali per questo nesting
                    num_odl = random.randint(2, 6)
                    selected_odl = random.sample(odl_ids, min(num_odl, len(odl_ids)))
                    
                    peso_totale = round(random.uniform(5.0, 25.0), 2)
                    efficienza = round(random.uniform(0.6, 0.95), 3) if stato in ['finito', 'completato'] else None
                    
                    # Data di creazione negli ultimi 30 giorni
                    created_at = datetime.now() - timedelta(days=random.randint(0, 30))
                    
                    cursor.execute("""
                        INSERT INTO nesting (
                            id, stato, autoclave_id, autoclave_nome, peso_totale, efficienza, 
                            odl_inclusi, valvole_utilizzate, valvole_totali, area_utilizzata, area_totale,
                            ciclo_cura, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nesting_id, stato, autoclave[0], autoclave[1], peso_totale, efficienza,
                        len(selected_odl), random.randint(2, 6), 6, 
                        round(random.uniform(1000, 3000), 0), 3000,
                        f"Ciclo_{random.choice(['A', 'B', 'C'])}", created_at.isoformat()
                    ))
                    
                    # Crea le relazioni nesting_odl
                    for odl_id in selected_odl:
                        cursor.execute("""
                            INSERT INTO nesting_odl (nesting_id, odl_id, posizione_x, posizione_y, rotazione)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            nesting_id, odl_id, 
                            random.randint(0, 1500), random.randint(0, 1200), 
                            random.choice([0, 90, 180, 270])
                        ))
                
                print(f"   ✅ Creati 10 nesting di test")
            else:
                print("   ⚠️ Impossibile creare nesting: mancano autoclavi o ODL")
        
        conn.commit()
        conn.close()
        print("\n✅ Dati di test creati con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante la creazione dei dati: {e}")

def main():
    """Funzione principale"""
    nesting_count, odl_count, autoclave_count = check_database()
    
    # Se il database è vuoto o quasi vuoto, crea dati di test
    if nesting_count == 0 or odl_count < 10:
        print("\n⚠️ Database vuoto o con pochi dati")
        create_test_data()
        print("\n🔄 Verifica finale...")
        check_database()
    else:
        print("\n✅ Database contiene già dati sufficienti per i test")

if __name__ == "__main__":
    main() 