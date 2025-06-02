#!/usr/bin/env python3
"""
Script per rimuovere manualmente le colonne del secondo piano dal database
"""
import sqlite3
import os

def remove_second_plane_columns():
    """Rimuove le colonne del secondo piano dal database"""
    
    db_path = 'carbonpilot.db'
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return False
    
    print("🗄️ RIMOZIONE COLONNE SECONDO PIANO")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Backup del database
        print("📋 Creazione backup...")
        cursor.execute("VACUUM INTO 'carbonpilot_backup.db'")
        print("✅ Backup creato: carbonpilot_backup.db")
        
        # Verifica colonne esistenti
        print("\n🔍 Verifica colonne esistenti...")
        
        cursor.execute("PRAGMA table_info(autoclavi)")
        autoclave_columns = [row[1] for row in cursor.fetchall()]
        print(f"Colonne autoclavi: {autoclave_columns}")
        
        cursor.execute("PRAGMA table_info(nesting_results)")
        nesting_columns = [row[1] for row in cursor.fetchall()]
        print(f"Colonne nesting_results: {nesting_columns}")
        
        # Rimuovi use_secondary_plane da autoclavi
        if 'use_secondary_plane' in autoclave_columns:
            print("\n🔧 Rimozione use_secondary_plane da autoclavi...")
            
            # SQLite non supporta DROP COLUMN direttamente, dobbiamo ricreare la tabella
            # 1. Crea tabella temporanea senza la colonna
            cursor.execute("""
                CREATE TABLE autoclavi_temp AS 
                SELECT id, nome, codice, lunghezza, larghezza_piano, num_linee_vuoto, 
                       temperatura_max, pressione_max, max_load_kg, stato, produttore, 
                       anno_produzione, note, created_at, updated_at
                FROM autoclavi
            """)
            
            # 2. Elimina tabella originale
            cursor.execute("DROP TABLE autoclavi")
            
            # 3. Rinomina tabella temporanea
            cursor.execute("ALTER TABLE autoclavi_temp RENAME TO autoclavi")
            
            print("✅ Colonna use_secondary_plane rimossa da autoclavi")
        else:
            print("ℹ️ Colonna use_secondary_plane già assente da autoclavi")
        
        # Rimuovi area_piano_2 e superficie_piano_2_max da nesting_results
        columns_to_remove = ['area_piano_2', 'superficie_piano_2_max']
        columns_present = [col for col in columns_to_remove if col in nesting_columns]
        
        if columns_present:
            print(f"\n🔧 Rimozione {columns_present} da nesting_results...")
            
            # Ottieni tutte le colonne tranne quelle da rimuovere
            remaining_columns = [col for col in nesting_columns if col not in columns_to_remove]
            columns_str = ', '.join(remaining_columns)
            
            # 1. Crea tabella temporanea senza le colonne
            cursor.execute(f"""
                CREATE TABLE nesting_results_temp AS 
                SELECT {columns_str}
                FROM nesting_results
            """)
            
            # 2. Elimina tabella originale
            cursor.execute("DROP TABLE nesting_results")
            
            # 3. Rinomina tabella temporanea
            cursor.execute("ALTER TABLE nesting_results_temp RENAME TO nesting_results")
            
            print(f"✅ Colonne {columns_present} rimosse da nesting_results")
        else:
            print("ℹ️ Colonne secondo piano già assenti da nesting_results")
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica finale
        print("\n✅ VERIFICA FINALE")
        print("=" * 20)
        
        cursor.execute("PRAGMA table_info(autoclavi)")
        new_autoclave_columns = [row[1] for row in cursor.fetchall()]
        print(f"Nuove colonne autoclavi: {new_autoclave_columns}")
        
        cursor.execute("PRAGMA table_info(nesting_results)")
        new_nesting_columns = [row[1] for row in cursor.fetchall()]
        print(f"Nuove colonne nesting_results: {new_nesting_columns}")
        
        # Verifica che le colonne siano state rimosse
        success = True
        if 'use_secondary_plane' in new_autoclave_columns:
            print("❌ ERRORE: use_secondary_plane ancora presente")
            success = False
        
        for col in columns_to_remove:
            if col in new_nesting_columns:
                print(f"❌ ERRORE: {col} ancora presente")
                success = False
        
        if success:
            print("🎉 TUTTE LE COLONNE RIMOSSE CON SUCCESSO!")
        
        conn.close()
        return success
        
    except Exception as e:
        print(f"❌ ERRORE: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = remove_second_plane_columns()
    exit(0 if success else 1) 