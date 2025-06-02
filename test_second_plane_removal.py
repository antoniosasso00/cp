#!/usr/bin/env python3
"""
Test per verificare la rimozione completa dei riferimenti al secondo piano
"""
import os
import sys
import sqlite3
import json
from pathlib import Path

def test_backend_models():
    """Testa che i modelli backend non abbiano più riferimenti al secondo piano"""
    print("🔍 TESTING BACKEND MODELS")
    print("=" * 40)
    
    # Test modello Autoclave
    try:
        sys.path.append('backend')
        from backend.models.autoclave import Autoclave
        
        # Verifica che use_secondary_plane non esista più
        autoclave_fields = [attr for attr in dir(Autoclave) if not attr.startswith('_')]
        
        if 'use_secondary_plane' in autoclave_fields:
            print("❌ ERRORE: Campo use_secondary_plane ancora presente in Autoclave")
            return False
        else:
            print("✅ Campo use_secondary_plane rimosso da Autoclave")
            
    except Exception as e:
        print(f"❌ Errore nel test modello Autoclave: {e}")
        return False
    
    # Test modello NestingResult
    try:
        from backend.models.nesting_result import NestingResult
        
        # Verifica che i campi del secondo piano non esistano più
        nesting_fields = [attr for attr in dir(NestingResult) if not attr.startswith('_')]
        
        removed_fields = ['area_piano_2', 'superficie_piano_2_max', 'efficienza_piano_2']
        errors = []
        
        for field in removed_fields:
            if field in nesting_fields:
                errors.append(field)
        
        if errors:
            print(f"❌ ERRORE: Campi ancora presenti in NestingResult: {errors}")
            return False
        else:
            print("✅ Campi secondo piano rimossi da NestingResult")
            
    except Exception as e:
        print(f"❌ Errore nel test modello NestingResult: {e}")
        return False
    
    return True

def test_database_schema():
    """Testa che lo schema database non abbia più le colonne del secondo piano"""
    print("\n🗄️ TESTING DATABASE SCHEMA")
    print("=" * 40)
    
    try:
        # Connessione al database
        db_path = 'backend/carbonpilot.db'
        if not os.path.exists(db_path):
            db_path = 'carbonpilot.db'
            
        if not os.path.exists(db_path):
            print("⚠️ Database non trovato, skip test schema")
            return True
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test tabella autoclavi
        cursor.execute("PRAGMA table_info(autoclavi)")
        autoclave_columns = [row[1] for row in cursor.fetchall()]
        
        if 'use_secondary_plane' in autoclave_columns:
            print("❌ ERRORE: Colonna use_secondary_plane ancora presente in autoclavi")
            return False
        else:
            print("✅ Colonna use_secondary_plane rimossa da autoclavi")
        
        # Test tabella nesting_results
        cursor.execute("PRAGMA table_info(nesting_results)")
        nesting_columns = [row[1] for row in cursor.fetchall()]
        
        removed_columns = ['area_piano_2', 'superficie_piano_2_max']
        errors = []
        
        for column in removed_columns:
            if column in nesting_columns:
                errors.append(column)
        
        if errors:
            print(f"❌ ERRORE: Colonne ancora presenti in nesting_results: {errors}")
            return False
        else:
            print("✅ Colonne secondo piano rimosse da nesting_results")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test database: {e}")
        return False

def test_frontend_interfaces():
    """Testa che le interfacce frontend non abbiano più riferimenti al secondo piano"""
    print("\n🎨 TESTING FRONTEND INTERFACES")
    print("=" * 40)
    
    try:
        # Test file nesting page
        nesting_page_path = 'frontend/src/app/dashboard/curing/nesting/page.tsx'
        
        if os.path.exists(nesting_page_path):
            with open(nesting_page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cerca riferimenti al secondo piano
            second_plane_refs = [
                'use_secondary_plane',
                'Piano secondario',
                'second_plane',
                'secondary_plane'
            ]
            
            found_refs = []
            for ref in second_plane_refs:
                if ref in content:
                    found_refs.append(ref)
            
            if found_refs:
                print(f"❌ ERRORE: Riferimenti secondo piano trovati in nesting page: {found_refs}")
                return False
            else:
                print("✅ Riferimenti secondo piano rimossi da nesting page")
        else:
            print("⚠️ File nesting page non trovato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test frontend: {e}")
        return False

def test_migration_exists():
    """Verifica che la migrazione per rimuovere le colonne esista"""
    print("\n📋 TESTING ALEMBIC MIGRATION")
    print("=" * 40)
    
    try:
        migration_path = 'backend/alembic/versions/remove_second_plane_columns.py'
        
        if os.path.exists(migration_path):
            with open(migration_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verifica che la migrazione contenga le operazioni corrette
            required_operations = [
                "drop_column('autoclavi', 'use_secondary_plane')",
                "drop_column('nesting_results', 'area_piano_2')",
                "drop_column('nesting_results', 'superficie_piano_2_max')"
            ]
            
            missing_operations = []
            for operation in required_operations:
                if operation not in content:
                    missing_operations.append(operation)
            
            if missing_operations:
                print(f"❌ ERRORE: Operazioni mancanti nella migrazione: {missing_operations}")
                return False
            else:
                print("✅ Migrazione remove_second_plane_columns creata correttamente")
        else:
            print("❌ ERRORE: Migrazione remove_second_plane_columns non trovata")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test migrazione: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("🧹 TEST RIMOZIONE SECONDO PIANO")
    print("=" * 50)
    
    tests = [
        ("Backend Models", test_backend_models),
        ("Database Schema", test_database_schema),
        ("Frontend Interfaces", test_frontend_interfaces),
        ("Alembic Migration", test_migration_exists)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERRORE in {test_name}: {e}")
            results.append((test_name, False))
    
    # Riepilogo risultati
    print("\n📊 RIEPILOGO RISULTATI")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RISULTATO FINALE: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 TUTTI I TEST PASSATI! Rimozione secondo piano completata con successo.")
        return True
    else:
        print("⚠️ Alcuni test falliti. Verificare i problemi sopra riportati.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 