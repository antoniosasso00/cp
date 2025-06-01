#!/usr/bin/env python3
"""
Script per verificare lo stato del database CarbonPilot
e identificare eventuali problemi o incoerenze
"""

import sys
import os
sys.path.append('./backend')

from models.db import test_database_connection, engine, SessionLocal
from sqlalchemy import text, inspect
import json

def check_database_structure():
    """Verifica la struttura del database"""
    print("🔍 Verifica struttura database...")
    
    try:
        # Test connessione
        if not test_database_connection():
            print("❌ Connessione al database fallita")
            return False
        
        # Ispeziona le tabelle
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Tabelle trovate: {len(tables)}")
        
        table_info = {}
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            table_info[table] = {
                'columns': len(columns),
                'column_names': [col['name'] for col in columns]
            }
            print(f"  📋 {table}: {len(columns)} colonne")
        
        return True, table_info
        
    except Exception as e:
        print(f"❌ Errore verifica struttura: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}

def check_data_integrity():
    """Verifica l'integrità dei dati"""
    print("\n🔍 Verifica integrità dati...")
    
    try:
        db = SessionLocal()
        
        # Verifica conteggi record per tabella
        tables_to_check = [
            'autoclavi', 'cataloghi', 'cicli_cura', 'parti', 'tools', 
            'odl', 'nesting_results', 'system_logs'
        ]
        
        data_integrity = {}
        
        for table in tables_to_check:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                data_integrity[table] = count
                print(f"  📊 {table}: {count} record")
            except Exception as e:
                print(f"  ❌ Errore tabella {table}: {str(e)}")
                data_integrity[table] = f"ERROR: {str(e)}"
        
        # Verifica foreign key integrity
        print("\n🔍 Verifica foreign keys...")
        
        # ODL -> Parte
        try:
            result = db.execute(text("""
                SELECT COUNT(*) FROM odl o 
                LEFT JOIN parti p ON o.parte_id = p.id 
                WHERE p.id IS NULL
            """))
            orphaned_odl = result.scalar()
            if orphaned_odl > 0:
                print(f"  ⚠️  ODL orfani (senza parte): {orphaned_odl}")
            else:
                print(f"  ✅ ODL-Parte integrity: OK")
        except Exception as e:
            print(f"  ❌ Errore check ODL-Parte: {str(e)}")
        
        # ODL -> Tool
        try:
            result = db.execute(text("""
                SELECT COUNT(*) FROM odl o 
                LEFT JOIN tools t ON o.tool_id = t.id 
                WHERE t.id IS NULL
            """))
            orphaned_odl_tools = result.scalar()
            if orphaned_odl_tools > 0:
                print(f"  ⚠️  ODL orfani (senza tool): {orphaned_odl_tools}")
            else:
                print(f"  ✅ ODL-Tool integrity: OK")
        except Exception as e:
            print(f"  ❌ Errore check ODL-Tool: {str(e)}")
        
        # NestingResult -> Autoclave
        try:
            result = db.execute(text("""
                SELECT COUNT(*) FROM nesting_results nr 
                LEFT JOIN autoclavi a ON nr.autoclave_id = a.id 
                WHERE a.id IS NULL
            """))
            orphaned_nesting = result.scalar()
            if orphaned_nesting > 0:
                print(f"  ⚠️  NestingResult orfani (senza autoclave): {orphaned_nesting}")
            else:
                print(f"  ✅ NestingResult-Autoclave integrity: OK")
        except Exception as e:
            print(f"  ❌ Errore check NestingResult-Autoclave: {str(e)}")
        
        db.close()
        return True, data_integrity
        
    except Exception as e:
        print(f"❌ Errore verifica integrità: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}

def test_admin_endpoints():
    """Testa l'accessibilità degli endpoint di amministrazione"""
    print("\n🔍 Test endpoint amministrativi...")
    
    try:
        # Importa i moduli necessari per testare gli endpoint
        from api.routers.admin import router
        print("  ✅ Router admin importato correttamente")
        
        # Test import del servizio di logging
        from services.system_log_service import SystemLogService
        print("  ✅ SystemLogService importato correttamente")
        
        # Test import modelli
        from models.system_log import SystemLog, UserRole, EventType, LogLevel
        print("  ✅ Modelli SystemLog importati correttamente")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Errore import endpoint admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale di verifica"""
    print("🚀 VERIFICA STATO DATABASE CARBONPILOT")
    print("=" * 50)
    
    # Test struttura database
    struct_ok, table_info = check_database_structure()
    
    # Test integrità dati
    data_ok, data_integrity = check_data_integrity()
    
    # Test endpoint admin
    admin_ok = test_admin_endpoints()
    
    # Risultato finale
    print("\n" + "=" * 50)
    print("📋 RIASSUNTO VERIFICA:")
    print(f"  🗃️  Struttura database: {'✅ OK' if struct_ok else '❌ ERRORE'}")
    print(f"  🔗 Integrità dati: {'✅ OK' if data_ok else '❌ ERRORE'}")
    print(f"  🔧 Endpoint admin: {'✅ OK' if admin_ok else '❌ ERRORE'}")
    
    if struct_ok and data_ok and admin_ok:
        print("\n🎉 Database verificato con successo!")
        print("   Pronto per testare le funzioni di backup/restore/reset")
    else:
        print("\n⚠️  Database presenta alcuni problemi")
        print("   Risolvi i problemi prima di procedere con backup/restore/reset")
    
    # Salva report dettagliato
    report = {
        'timestamp': str(sys.modules['datetime'].datetime.now()) if 'datetime' in sys.modules else 'N/A',
        'structure_ok': struct_ok,
        'data_integrity_ok': data_ok,
        'admin_endpoints_ok': admin_ok,
        'table_info': table_info,
        'data_integrity': data_integrity
    }
    
    try:
        with open('database_check_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Report salvato in: database_check_report.json")
    except Exception as e:
        print(f"\n⚠️  Impossibile salvare report: {str(e)}")

if __name__ == "__main__":
    main() 