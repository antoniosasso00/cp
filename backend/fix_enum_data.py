#!/usr/bin/env python3
"""
Script per correggere i valori enum nel database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from models.db import get_database_url

def fix_enum_values():
    """Corregge i valori enum nel database."""
    
    print("🔧 CORREZIONE VALORI ENUM")
    print("=" * 50)
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # 1. Verifica i valori attuali
            print("📊 Valori attuali in schedule_entries:")
            result = conn.execute(text("SELECT DISTINCT schedule_type FROM schedule_entries WHERE schedule_type IS NOT NULL"))
            current_types = [row[0] for row in result]
            print(f"  schedule_type: {current_types}")
            
            result = conn.execute(text("SELECT DISTINCT status FROM schedule_entries"))
            current_statuses = [row[0] for row in result]
            print(f"  status: {current_statuses}")
            
            # 2. Mapping per correggere i valori
            type_mapping = {
                'ODL_SPECIFICO': 'odl_specifico',
                'CATEGORIA': 'categoria', 
                'SOTTO_CATEGORIA': 'sotto_categoria',
                'RICORRENTE': 'ricorrente'
            }
            
            status_mapping = {
                'SCHEDULED': 'scheduled',
                'MANUAL': 'manual',
                'PREVISIONALE': 'previsionale',
                'IN_ATTESA': 'in_attesa',
                'IN_CORSO': 'in_corso',
                'DONE': 'done',
                'POSTICIPATO': 'posticipato'
            }
            
            # 3. Correggi schedule_type
            print("\n🔄 Correzione schedule_type:")
            for old_value, new_value in type_mapping.items():
                result = conn.execute(text(f"""
                    UPDATE schedule_entries 
                    SET schedule_type = '{new_value}' 
                    WHERE schedule_type = '{old_value}'
                """))
                if result.rowcount > 0:
                    print(f"  ✅ {old_value} → {new_value} ({result.rowcount} record)")
            
            # 4. Correggi status
            print("\n🔄 Correzione status:")
            for old_value, new_value in status_mapping.items():
                result = conn.execute(text(f"""
                    UPDATE schedule_entries 
                    SET status = '{new_value}' 
                    WHERE status = '{old_value}'
                """))
                if result.rowcount > 0:
                    print(f"  ✅ {old_value} → {new_value} ({result.rowcount} record)")
            
            # 5. Imposta valori di default per campi NULL
            print("\n🔄 Impostazione valori di default:")
            
            # schedule_type default
            result = conn.execute(text("""
                UPDATE schedule_entries 
                SET schedule_type = 'odl_specifico' 
                WHERE schedule_type IS NULL
            """))
            if result.rowcount > 0:
                print(f"  ✅ schedule_type NULL → odl_specifico ({result.rowcount} record)")
            
            # is_recurring default
            result = conn.execute(text("""
                UPDATE schedule_entries 
                SET is_recurring = 0 
                WHERE is_recurring IS NULL
            """))
            if result.rowcount > 0:
                print(f"  ✅ is_recurring NULL → false ({result.rowcount} record)")
            
            # priority_override default
            result = conn.execute(text("""
                UPDATE schedule_entries 
                SET priority_override = 0 
                WHERE priority_override IS NULL
            """))
            if result.rowcount > 0:
                print(f"  ✅ priority_override NULL → false ({result.rowcount} record)")
            
            # 6. Rendi odl_id nullable
            print("\n🔄 Correzione vincoli:")
            try:
                # Per SQLite, non possiamo modificare direttamente i vincoli
                # Ma possiamo verificare se ci sono problemi
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM schedule_entries 
                    WHERE schedule_type != 'odl_specifico' AND odl_id IS NOT NULL
                """))
                non_odl_with_odl_id = result.scalar()
                
                if non_odl_with_odl_id > 0:
                    print(f"  ⚠️  {non_odl_with_odl_id} record non-ODL hanno odl_id (normale)")
                
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM schedule_entries 
                    WHERE schedule_type = 'odl_specifico' AND odl_id IS NULL
                """))
                odl_without_odl_id = result.scalar()
                
                if odl_without_odl_id > 0:
                    print(f"  ❌ {odl_without_odl_id} record ODL_SPECIFICO senza odl_id")
                    # Questi devono essere corretti manualmente o eliminati
                
            except Exception as e:
                print(f"  ⚠️  Errore verifica vincoli: {e}")
            
            # Commit delle modifiche
            conn.commit()
            
            # 7. Verifica finale
            print("\n📊 Valori dopo correzione:")
            result = conn.execute(text("SELECT DISTINCT schedule_type FROM schedule_entries WHERE schedule_type IS NOT NULL"))
            new_types = [row[0] for row in result]
            print(f"  schedule_type: {new_types}")
            
            result = conn.execute(text("SELECT DISTINCT status FROM schedule_entries"))
            new_statuses = [row[0] for row in result]
            print(f"  status: {new_statuses}")
            
            print("\n✅ Correzione enum completata!")
            return True
            
    except Exception as e:
        print(f"❌ Errore durante la correzione: {e}")
        return False

def main():
    """Esegue la correzione degli enum."""
    
    print("🚀 AVVIO CORREZIONE ENUM")
    print("=" * 40)
    
    if fix_enum_values():
        print("\n🎉 Correzione completata con successo!")
        print("\n📋 Prossimi passi:")
        print("1. Riavvia il backend: py main.py")
        print("2. Testa l'endpoint: curl http://localhost:8000/api/v1/schedules")
    else:
        print("\n❌ Correzione fallita")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 