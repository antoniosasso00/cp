#!/usr/bin/env python3
"""
Script per analizzare la struttura del database CarbonPilot
"""

import sqlite3

def analyze_database():
    """Analizza la struttura del database"""
    print("🔍 Analisi Struttura Database CarbonPilot")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Ottieni tutte le tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tabelle trovate ({len(tables)}):")
        for table in tables:
            print(f"   - {table}")
        
        # Analizza le tabelle più importanti per il nesting
        important_tables = ['nesting_results', 'odl', 'autoclavi', 'nesting_result_odl']
        
        for table in important_tables:
            if table in tables:
                print(f"\n📊 Struttura tabella '{table}':")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PK' if col[5] else ''}")
                
                # Conta i record
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📈 Record totali: {count}")
                
                # Mostra alcuni esempi se ci sono dati
                if count > 0 and count <= 10:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    examples = cursor.fetchall()
                    print(f"   📝 Esempi di dati:")
                    for i, example in enumerate(examples):
                        print(f"      {i+1}: {example}")
        
        # Verifica specificamente i nesting_results
        print(f"\n🎯 Analisi dettagliata nesting_results:")
        cursor.execute("SELECT COUNT(*) FROM nesting_results")
        nesting_count = cursor.fetchone()[0]
        print(f"   Totale nesting_results: {nesting_count}")
        
        if nesting_count > 0:
            # Verifica gli stati disponibili
            cursor.execute("SELECT DISTINCT stato FROM nesting_results")
            stati = [row[0] for row in cursor.fetchall()]
            print(f"   Stati disponibili: {stati}")
            
            # Conta per stato
            for stato in stati:
                cursor.execute("SELECT COUNT(*) FROM nesting_results WHERE stato = ?", (stato,))
                count = cursor.fetchone()[0]
                print(f"      {stato}: {count}")
            
            # Mostra alcuni nesting di esempio
            cursor.execute("""
                SELECT id, stato, autoclave_id, peso_totale, efficienza, created_at 
                FROM nesting_results 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            recent_nestings = cursor.fetchall()
            print(f"\n   📊 Ultimi 5 nesting_results:")
            for nesting in recent_nestings:
                print(f"      ID: {nesting[0]} | Stato: {nesting[1]} | Autoclave: {nesting[2]} | Peso: {nesting[3]} | Efficienza: {nesting[4]}")
        
        # Verifica le relazioni nesting-odl
        print(f"\n🔗 Analisi relazioni nesting_result_odl:")
        cursor.execute("SELECT COUNT(*) FROM nesting_result_odl")
        relations_count = cursor.fetchone()[0]
        print(f"   Totale relazioni: {relations_count}")
        
        if relations_count > 0:
            cursor.execute("""
                SELECT nr.id, nr.stato, COUNT(nro.odl_id) as odl_count
                FROM nesting_results nr
                LEFT JOIN nesting_result_odl nro ON nr.id = nro.nesting_result_id
                GROUP BY nr.id, nr.stato
                ORDER BY nr.created_at DESC
                LIMIT 5
            """)
            nesting_with_odl = cursor.fetchall()
            print(f"   📊 Nesting con ODL associati:")
            for item in nesting_with_odl:
                print(f"      Nesting {item[0]} ({item[1]}): {item[2]} ODL")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {e}")

if __name__ == "__main__":
    analyze_database() 