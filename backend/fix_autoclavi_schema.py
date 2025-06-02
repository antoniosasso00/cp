#!/usr/bin/env python3
"""
Script per rimuovere la colonna use_secondary_plane dalla tabella autoclavi
"""
import sqlite3
import os
import shutil
from datetime import datetime

def fix_autoclavi_schema():
    """Rimuove la colonna use_secondary_plane dalla tabella autoclavi"""
    
    # Trova il database
    db_paths = ['carbonpilot.db', '../carbonpilot.db', './carbonpilot.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database non trovato")
        return False
    
    print(f"🔧 FIX SCHEMA AUTOCLAVI")
    print(f"Database: {db_path}")
    print("=" * 50)
    
    # Backup del database
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup creato: {backup_path}")
    except Exception as e:
        print(f"❌ Errore backup: {e}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 Stato PRIMA delle modifiche:")
        cursor.execute("PRAGMA table_info(autoclavi)")
        columns_before = [row[1] for row in cursor.fetchall()]
        print(f"Colonne: {', '.join(columns_before)}")
        print(f"use_secondary_plane presente: {'use_secondary_plane' in columns_before}")
        
        if 'use_secondary_plane' not in columns_before:
            print("✅ La colonna use_secondary_plane non esiste - nessuna azione necessaria")
            conn.close()
            return True
        
        print("\n🔧 Rimozione colonna use_secondary_plane...")
        
        # SQLite non supporta DROP COLUMN direttamente
        # Dobbiamo ricreare la tabella senza quella colonna
        
        # 1. Recupera tutti i dati esistenti
        cursor.execute("SELECT * FROM autoclavi")
        all_data = cursor.fetchall()
        print(f"📊 Trovati {len(all_data)} record da preservare")
        
        # 2. Ottieni le colonne che vogliamo mantenere (tutte tranne use_secondary_plane)
        target_columns = [col for col in columns_before if col != 'use_secondary_plane']
        target_columns_str = ', '.join(target_columns)
        
        print(f"📋 Colonne da mantenere: {target_columns_str}")
        
        # 3. Trova gli indici delle colonne da mantenere
        column_indices = [columns_before.index(col) for col in target_columns]
        
        # 4. Crea la tabella temporanea con lo schema corretto
        create_temp_sql = f"""
        CREATE TABLE autoclavi_temp (
            id INTEGER PRIMARY KEY,
            nome VARCHAR(100) UNIQUE NOT NULL,
            codice VARCHAR(50) UNIQUE,
            lunghezza FLOAT,
            larghezza_piano FLOAT,
            temperatura_max FLOAT,
            pressione_max FLOAT,
            max_load_kg FLOAT DEFAULT 1000.0,
            num_linee_vuoto INTEGER,
            stato VARCHAR(12) NOT NULL DEFAULT 'DISPONIBILE',
            produttore VARCHAR(100),
            anno_produzione INTEGER,
            note TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
        """
        
        cursor.execute(create_temp_sql)
        print("✅ Tabella temporanea creata")
        
        # 5. Inserisci i dati filtrati nella tabella temporanea
        if all_data:
            # Prepara i placeholder per l'INSERT
            placeholders = ', '.join(['?' for _ in target_columns])
            insert_sql = f"INSERT INTO autoclavi_temp ({target_columns_str}) VALUES ({placeholders})"
            
            # Filtra i dati per rimuovere la colonna use_secondary_plane
            filtered_data = []
            for row in all_data:
                filtered_row = tuple(row[i] for i in column_indices)
                filtered_data.append(filtered_row)
            
            cursor.executemany(insert_sql, filtered_data)
            print(f"✅ {len(filtered_data)} record inseriti nella tabella temporanea")
        
        # 6. Elimina la tabella originale
        cursor.execute("DROP TABLE autoclavi")
        print("✅ Tabella originale eliminata")
        
        # 7. Rinomina la tabella temporanea
        cursor.execute("ALTER TABLE autoclavi_temp RENAME TO autoclavi")
        print("✅ Tabella temporanea rinominata")
        
        # 8. Ricrea gli indici se necessario
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_autoclavi_nome ON autoclavi (nome)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_autoclavi_codice ON autoclavi (codice)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_autoclavi_id ON autoclavi (id)")
        print("✅ Indici ricreati")
        
        # Commit delle modifiche
        conn.commit()
        
        print("\n🔍 Stato DOPO le modifiche:")
        cursor.execute("PRAGMA table_info(autoclavi)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"Colonne: {', '.join(columns_after)}")
        print(f"use_secondary_plane presente: {'use_secondary_plane' in columns_after}")
        
        # Verifica conteggio record
        cursor.execute("SELECT COUNT(*) FROM autoclavi")
        count_after = cursor.fetchone()[0]
        print(f"Record dopo modifica: {count_after}")
        
        conn.close()
        
        print("\n✅ SCHEMA AUTOCLAVI CORRETTO CON SUCCESSO!")
        print(f"   - Colonna use_secondary_plane rimossa")
        print(f"   - {count_after} record preservati")
        print(f"   - Backup disponibile: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la modifica: {str(e)}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        
        # Ripristina il backup in caso di errore
        try:
            shutil.copy2(backup_path, db_path)
            print(f"🔄 Database ripristinato dal backup")
        except Exception as restore_error:
            print(f"❌ Errore ripristino backup: {restore_error}")
        
        return False

if __name__ == "__main__":
    success = fix_autoclavi_schema()
    if success:
        print("\n🎉 Fix completato con successo!")
    else:
        print("\n❌ Fix fallito - controllare i messaggi di errore") 