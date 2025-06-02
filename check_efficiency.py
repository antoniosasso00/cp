import sqlite3

def check_efficiency_field():
    """Verifica se il campo efficiency esiste nella tabella batch_nesting"""
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Ottieni informazioni sulla tabella
        cursor.execute("PRAGMA table_info(batch_nesting)")
        columns = cursor.fetchall()
        
        print("🔍 Colonne nella tabella batch_nesting:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print(f"\n📊 Totale colonne: {len(columns)}")
        
        # Verifica se esiste il campo efficiency
        efficiency_exists = any(col[1] == 'efficiency' for col in columns)
        
        if efficiency_exists:
            print("✅ Campo 'efficiency' trovato!")
            
            # Verifica se ci sono batch esistenti
            cursor.execute("SELECT COUNT(*) FROM batch_nesting")
            count = cursor.fetchone()[0]
            print(f"📊 Numero di batch nel database: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, efficiency FROM batch_nesting LIMIT 3")
                batches = cursor.fetchall()
                print("🎯 Primi 3 batch con efficienza:")
                for batch in batches:
                    print(f"  - ID: {batch[0]}, Efficienza: {batch[1]}")
        else:
            print("❌ Campo 'efficiency' NON trovato!")
            print("💡 È necessario applicare la migrazione per aggiungere il campo")
            
            # Verifica se ci sono batch esistenti
            cursor.execute("SELECT COUNT(*) FROM batch_nesting")
            count = cursor.fetchone()[0]
            print(f"📊 Numero di batch nel database: {count}")
        
        conn.close()
        return efficiency_exists
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def add_efficiency_field():
    """Aggiunge manualmente il campo efficiency alla tabella"""
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        print("🔧 Aggiunta del campo efficiency...")
        cursor.execute("ALTER TABLE batch_nesting ADD COLUMN efficiency REAL DEFAULT 0.0")
        
        print("🔄 Aggiornamento dei record esistenti...")
        cursor.execute("UPDATE batch_nesting SET efficiency = 0.0 WHERE efficiency IS NULL")
        
        conn.commit()
        conn.close()
        
        print("✅ Campo efficiency aggiunto con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore nell'aggiunta del campo: {e}")
        return False

if __name__ == "__main__":
    print("🧪 VERIFICA E AGGIUNTA CAMPO EFFICIENCY")
    print("=" * 50)
    
    if not check_efficiency_field():
        print("\n🔧 Tentativo di aggiungere il campo efficiency...")
        if add_efficiency_field():
            print("\n🔍 Verifica finale:")
            check_efficiency_field()
    else:
        print("\n✅ Il campo efficiency è già presente!") 