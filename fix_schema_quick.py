import sqlite3

print("Fixing database schema...")

try:
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    # Verifica se la colonna esiste
    cursor.execute('PRAGMA table_info(odl)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'include_in_std' not in columns:
        print("Adding include_in_std column...")
        cursor.execute('ALTER TABLE odl ADD COLUMN include_in_std BOOLEAN NOT NULL DEFAULT 1')
        print("Column added!")
    else:
        print("Column already exists!")
    
    # Verifica tabella standard_times
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='standard_times'")
    if not cursor.fetchone():
        print("Creating standard_times table...")
        cursor.execute("""
            CREATE TABLE standard_times (
                id INTEGER PRIMARY KEY,
                part_number VARCHAR(50) NOT NULL,
                phase VARCHAR(50) NOT NULL,
                minutes FLOAT NOT NULL,
                note VARCHAR(500),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Aggiungi dati di test
        test_data = [
            ('TEST-E2E-001', 'laminazione', 45.0, 'Tempo standard laminazione'),
            ('TEST-E2E-001', 'cura', 120.0, 'Tempo standard cura'),
            ('TEST-E2E-001', 'attesa_cura', 30.0, 'Tempo standard attesa cura')
        ]
        
        cursor.executemany(
            "INSERT INTO standard_times (part_number, phase, minutes, note) VALUES (?, ?, ?, ?)",
            test_data
        )
        print("Table created and test data added!")
    else:
        print("standard_times table already exists!")
    
    conn.commit()
    conn.close()
    print("Schema fixed successfully!")
    
except Exception as e:
    print(f"Error: {e}") 