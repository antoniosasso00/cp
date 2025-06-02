#!/usr/bin/env python3
"""
Script per verificare i dati disponibili per il modulo di nesting
"""
import sqlite3
import json
from datetime import datetime

def check_nesting_data():
    """Controlla i dati disponibili per il nesting"""
    
    print("🔍 ANALISI DATI DISPONIBILI PER NESTING")
    print("=" * 50)
    
    # Connessione al database
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    try:
        # 1. Controlla ODL disponibili per il nesting
        print("📋 1. ANALISI ODL:")
        print("-" * 30)
        
        # Tutti gli stati ODL
        cursor.execute("SELECT status, COUNT(*) FROM odl GROUP BY status ORDER BY COUNT(*) DESC")
        stati_odl = cursor.fetchall()
        
        print("  Stati ODL nel database:")
        for stato, count in stati_odl:
            print(f"    {stato}: {count} ODL")
        
        # ODL con dettagli completi
        cursor.execute('''
            SELECT o.id, o.status, p.part_number, p.descrizione_breve, 
                   t.part_number_tool, t.larghezza_piano, t.lunghezza_piano, t.peso,
                   cc.nome as ciclo_cura
            FROM odl o
            JOIN parti p ON o.parte_id = p.id
            JOIN tools t ON o.tool_id = t.id
            LEFT JOIN cicli_cura cc ON p.ciclo_cura_id = cc.id
            WHERE o.status IN ('Attesa Cura', 'Preparazione', 'Pronto')
            ORDER BY o.id
        ''')
        
        odl_disponibili = cursor.fetchall()
        print(f"\n  ODL utilizzabili per nesting ({len(odl_disponibili)}):")
        
        if odl_disponibili:
            for row in odl_disponibili:
                print(f"    ODL #{row[0]} - {row[1]}")
                print(f"      Parte: {row[2]} ({row[3]})")
                print(f"      Tool: {row[4]} ({row[5]}x{row[6]}mm, {row[7]}kg)")
                print(f"      Ciclo: {row[8] or 'Non definito'}")
                print()
        else:
            print("    ❌ Nessun ODL utilizzabile trovato")
        
        # 2. Controlla autoclavi
        print("🏭 2. ANALISI AUTOCLAVI:")
        print("-" * 30)
        
        # Tutti gli stati autoclavi
        cursor.execute("SELECT stato, COUNT(*) FROM autoclavi GROUP BY stato")
        stati_autoclavi = cursor.fetchall()
        
        print("  Stati autoclavi nel database:")
        for stato, count in stati_autoclavi:
            print(f"    {stato}: {count} autoclavi")
        
        # Autoclavi disponibili
        cursor.execute('''
            SELECT id, nome, codice, stato, larghezza_piano, lunghezza, max_load_kg,
                   num_linee_vuoto
            FROM autoclavi
            WHERE stato = 'DISPONIBILE'
            ORDER BY id
        ''')
        
        autoclavi_disponibili = cursor.fetchall()
        print(f"\n  Autoclavi utilizzabili ({len(autoclavi_disponibili)}):")
        
        if autoclavi_disponibili:
            for row in autoclavi_disponibili:
                print(f"    Autoclave #{row[0]} - {row[1]} ({row[2]})")
                print(f"      Stato: {row[3]}")
                print(f"      Dimensioni: {row[4]}x{row[5]}mm")
                print(f"      Carico max: {row[6]}kg")
                print(f"      Linee vuoto: {row[7]}")
                print(f"      Piano secondario: Non più supportato")
                print()
        else:
            print("    ❌ Nessuna autoclave disponibile trovata")
        
        # 3. Compatibilità cicli di cura
        print("🔄 3. ANALISI COMPATIBILITÀ:")
        print("-" * 30)
        
        cursor.execute('''
            SELECT cc.id, cc.nome, COUNT(p.id) as parti_count,
                   cc.temperatura_stasi1, cc.pressione_stasi1, cc.durata_stasi1
            FROM cicli_cura cc
            LEFT JOIN parti p ON cc.id = p.ciclo_cura_id
            GROUP BY cc.id, cc.nome
            ORDER BY parti_count DESC
        ''')
        
        cicli_disponibili = cursor.fetchall()
        print("  Cicli di cura disponibili:")
        
        for row in cicli_disponibili:
            print(f"    Ciclo #{row[0]} - {row[1]}")
            print(f"      Parti associate: {row[2]}")
            print(f"      Parametri: {row[3]}°C, {row[4]}bar, {row[5]}min")
            print()
        
        # 4. Suggerimenti per il test
        print("💡 4. SUGGERIMENTI PER TEST:")
        print("-" * 30)
        
        if len(odl_disponibili) > 0 and len(autoclavi_disponibili) > 0:
            print("  ✅ DATI SUFFICIENTI PER TEST NESTING!")
            print(f"  📋 Usa ODL: {[row[0] for row in odl_disponibili[:3]]}")
            print(f"  🏭 Usa Autoclave: {autoclavi_disponibili[0][0]} ({autoclavi_disponibili[0][1]})")
            
            # Crea dati di test
            test_data = {
                "odl_ids": [str(row[0]) for row in odl_disponibili[:3]],
                "autoclave_ids": [str(autoclavi_disponibili[0][0])],
                "parametri": {
                    "padding_mm": 20,
                    "min_distance_mm": 15,
                    "priorita_area": True
                }
            }
            
            print("\n  📄 Dati di test JSON:")
            print(json.dumps(test_data, indent=2))
            
        else:
            print("  ❌ DATI INSUFFICIENTI - Creare ODL e autoclavi di test")
            
        # 5. Controlla batch nesting esistenti
        print("\n📦 5. BATCH NESTING ESISTENTI:")
        print("-" * 30)
        
        cursor.execute('''
            SELECT id, nome, stato, autoclave_id, created_at, numero_nesting
            FROM batch_nesting
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        
        batch_esistenti = cursor.fetchall()
        
        if batch_esistenti:
            print("  Ultimi batch nesting:")
            for row in batch_esistenti:
                print(f"    {row[0][:8]}... - {row[1]} - {row[2]} - Autoclave {row[3]} - {row[4]}")
        else:
            print("  Nessun batch nesting trovato")
            
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {str(e)}")
        
    finally:
        conn.close()
        
    print("\n" + "=" * 50)
    print("🎯 ANALISI COMPLETATA")

if __name__ == "__main__":
    check_nesting_data() 