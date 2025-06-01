#!/usr/bin/env python3
"""
Test diretto delle funzioni admin senza HTTP
"""

import sys
import os
sys.path.append('./backend')

from models.db import SessionLocal
from api.routers.admin import export_database, reset_database, get_database_info
from fastapi import UploadFile
import tempfile
import json

def test_database_info_direct():
    """Test diretto dell'endpoint database info"""
    print("🔍 Test diretto database info...")
    
    try:
        db = SessionLocal()
        result = await get_database_info(db)
        print(f"✅ Database info OK: {result['total_tables']} tabelle, {result['total_records']} record")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Errore database info: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_backup_direct():
    """Test diretto dell'endpoint backup"""
    print("\n🔍 Test diretto backup...")
    
    try:
        db = SessionLocal()
        response = await export_database(db)
        print(f"✅ Backup OK: tipo {type(response)}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Errore backup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_reset_direct():
    """Test diretto dell'endpoint reset"""
    print("\n🔍 Test diretto reset...")
    
    try:
        db = SessionLocal()
        result = await reset_database({"confirmation": "reset"}, db)
        print(f"✅ Reset OK: {result['total_deleted_records']} record eliminati")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Errore reset: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Funzione principale asincrona"""
    print("🚀 TEST DIRETTO FUNZIONI ADMIN")
    print("=" * 40)
    
    # Test database info
    info_ok = test_database_info_direct()
    
    # Test backup
    backup_ok = test_backup_direct()
    
    # Test reset
    reset_ok = test_reset_direct()
    
    print("\n" + "=" * 40)
    print("📋 RISULTATI:")
    print(f"  🔍 Database Info: {'✅ OK' if info_ok else '❌ ERRORE'}")
    print(f"  💾 Backup: {'✅ OK' if backup_ok else '❌ ERRORE'}")
    print(f"  🗑️  Reset: {'✅ OK' if reset_ok else '❌ ERRORE'}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 