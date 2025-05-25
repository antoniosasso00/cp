#!/usr/bin/env python3
"""
Script di debug per controllare i report nel database
"""

import sys
import os
from pathlib import Path

# Aggiungi il percorso del backend al PYTHONPATH
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from models.db import get_db
from models.report import Report, ReportTypeEnum

def debug_reports():
    """Debug dei report nel database"""
    
    print("🔍 Debug Reports Database")
    print("=" * 50)
    
    try:
        # Ottieni la sessione del database
        db = next(get_db())
        
        # Conta i report
        count = db.query(Report).count()
        print(f"📊 Numero totale di report: {count}")
        
        if count > 0:
            print("\n📋 Report esistenti:")
            reports = db.query(Report).all()
            
            for report in reports:
                print(f"  ID: {report.id}")
                print(f"  Filename: {report.filename}")
                print(f"  Type (raw): {report.report_type}")
                print(f"  Type (value): {report.report_type.value if hasattr(report.report_type, 'value') else 'N/A'}")
                print(f"  Created: {report.created_at}")
                print("  " + "-" * 40)
        
        # Test degli enum
        print("\n🔧 Test Enum Values:")
        for enum_val in ReportTypeEnum:
            print(f"  {enum_val.name} = '{enum_val.value}'")
        
        # Test di creazione enum
        print("\n🧪 Test conversione enum:")
        test_values = ["produzione", "PRODUZIONE", "nesting", "NESTING"]
        for val in test_values:
            try:
                enum_obj = ReportTypeEnum(val)
                print(f"  ✅ '{val}' -> {enum_obj}")
            except ValueError as e:
                print(f"  ❌ '{val}' -> ERROR: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Errore durante il debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_reports() 