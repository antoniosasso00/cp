#!/usr/bin/env python3
"""
Applica migrazione 2L direttamente al database
============================================
"""
import sqlite3
import os

def apply_2l_migration():
    db_path = '../carbonpilot.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} non trovato")
        return False
    
    print("🚀 Applicazione migrazione 2L al database...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica stato attuale
        cursor.execute('PRAGMA table_info(autoclavi)')
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"📋 Colonne attuali: {len(columns)}")
        
        # Campi da aggiungere
        if 'usa_cavalletti' not in columns:
            print("➕ Aggiungendo usa_cavalletti...")
            cursor.execute('ALTER TABLE autoclavi ADD COLUMN usa_cavalletti BOOLEAN DEFAULT 0 NOT NULL')
        
        if 'altezza_cavalletto_standard' not in columns:
            print("➕ Aggiungendo altezza_cavalletto_standard...")
            cursor.execute('ALTER TABLE autoclavi ADD COLUMN altezza_cavalletto_standard FLOAT')
            
        if 'max_cavalletti' not in columns:
            print("➕ Aggiungendo max_cavalletti...")
            cursor.execute('ALTER TABLE autoclavi ADD COLUMN max_cavalletti INTEGER DEFAULT 2')
            
        if 'clearance_verticale' not in columns:
            print("➕ Aggiungendo clearance_verticale...")
            cursor.execute('ALTER TABLE autoclavi ADD COLUMN clearance_verticale FLOAT')
        
        # Configura autoclavi per 2L
        print("🔧 Configurazione autoclavi...")
        
        # PANINI: Supporto cavalletti completo
        cursor.execute("""
            UPDATE autoclavi 
            SET usa_cavalletti = 1, 
                altezza_cavalletto_standard = 100.0,
                max_cavalletti = 4,
                clearance_verticale = 50.0
            WHERE nome LIKE '%PANINI%'
        """)
        
        # ISMAR: Supporto cavalletti limitato
        cursor.execute("""
            UPDATE autoclavi 
            SET usa_cavalletti = 1, 
                altezza_cavalletto_standard = 80.0,
                max_cavalletti = 2,
                clearance_verticale = 40.0
            WHERE nome LIKE '%ISMAR%'
        """)
        
        # MAROSO: Solo piano base
        cursor.execute("""
            UPDATE autoclavi 
            SET usa_cavalletti = 0, 
                max_cavalletti = 0
            WHERE nome LIKE '%MAROSO%'
        """)
        
        conn.commit()
        
        # Verifica risultato
        cursor.execute('SELECT nome, usa_cavalletti, altezza_cavalletto_standard, max_cavalletti FROM autoclavi')
        results = cursor.fetchall()
        
        print("\n📊 Configurazione autoclavi 2L:")
        for nome, usa_cav, altezza, max_cav in results:
            status = "✅ 2L ABILITATO" if usa_cav else "❌ Solo piano base"
            print(f"  {nome}: {status} (H:{altezza}mm, Max:{max_cav})")
        
        conn.close()
        print("\n✅ Migrazione 2L applicata con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    success = apply_2l_migration()
    if success:
        print("\n🎯 PROSSIMO PASSO: Riavviare il backend per caricare le modifiche")
        print("📋 Comando: Ctrl+C per terminare uvicorn, poi riavviare")
    exit(0 if success else 1) 