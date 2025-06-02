#!/usr/bin/env python3
"""
🔍 Analizza quale database viene utilizzato dal sistema
"""

import os
import sqlite3
from pathlib import Path

def analyze_databases():
    """Analizza i database presenti"""
    
    print('🔍 ANALISI DATABASE PRESENTI')
    print('=' * 40)
    
    # Database locations
    root_db = Path('./carbonpilot.db')
    backend_db = Path('./backend/carbonpilot.db')
    
    # Test database root
    if root_db.exists():
        print(f'📁 Database ROOT trovato: {root_db.absolute()}')
        print(f'   Dimensione: {root_db.stat().st_size / 1024:.1f} KB')
        
        # Test conteggio autoclavi in root
        try:
            with sqlite3.connect(str(root_db)) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM autoclavi')
                count_root = cursor.fetchone()[0]
            print(f'   Autoclavi: {count_root}')
        except Exception as e:
            print(f'   Errore: {e}')
    else:
        print('❌ Database ROOT non trovato')
    
    # Test database backend
    if backend_db.exists():
        print(f'\n📁 Database BACKEND trovato: {backend_db.absolute()}')
        print(f'   Dimensione: {backend_db.stat().st_size / 1024:.1f} KB')
        
        # Test conteggio autoclavi in backend
        try:
            with sqlite3.connect(str(backend_db)) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM autoclavi')
                count_backend = cursor.fetchone()[0]
            print(f'   Autoclavi: {count_backend}')
        except Exception as e:
            print(f'   Errore: {e}')
    else:
        print('❌ Database BACKEND non trovato')
    
    # Test quale database usa l'applicazione
    print(f'\n🎯 TEST DATABASE UTILIZZATO DALL\'APP:')
    print(f'   Working Directory: {os.getcwd()}')
    print(f'   Database path nell\'app: ./carbonpilot.db')
    app_db_path = Path('./carbonpilot.db').absolute()
    print(f'   Risolto come: {app_db_path}')
    
    # Test dal backend
    print(f'\n🎯 TEST DAL BACKEND:')
    backend_cwd = Path('./backend').absolute()
    print(f'   Backend Directory: {backend_cwd}')
    backend_app_db = backend_cwd / 'carbonpilot.db'
    print(f'   Database dal backend: {backend_app_db}')
    print(f'   Esiste: {backend_app_db.exists()}')
    
    return root_db.exists(), backend_db.exists()

def test_app_database():
    """Testa quale database usa l'app da root"""
    print(f'\n🧪 TEST DATABASE DALL\'APPLICAZIONE (da root):')
    
    # Simula l'uso dell'app dalla root
    os.chdir('.')  # Assicura che siamo nella root
    try:
        import sys
        sys.path.append('./backend')
        from backend.models.db import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        result = db.execute(text('SELECT COUNT(*) FROM autoclavi'))
        count = result.scalar()
        print(f'   ✅ Autoclavi trovate: {count}')
        
        # Trova il path reale del database
        db_path = Path('./carbonpilot.db').absolute()
        print(f'   📁 Database utilizzato: {db_path}')
        db.close()
        
        return True
    except Exception as e:
        print(f'   ❌ Errore: {e}')
        return False

def test_backend_database():
    """Testa quale database usa l'app dal backend"""
    print(f'\n🧪 TEST DATABASE DALL\'APPLICAZIONE (da backend):')
    
    # Cambia nella directory backend
    original_cwd = os.getcwd()
    try:
        os.chdir('./backend')
        
        import sys
        sys.path.append('.')
        from models.db import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        result = db.execute(text('SELECT COUNT(*) FROM autoclavi'))
        count = result.scalar()
        print(f'   ✅ Autoclavi trovate: {count}')
        
        # Trova il path reale del database
        db_path = Path('./carbonpilot.db').absolute()
        print(f'   📁 Database utilizzato: {db_path}')
        db.close()
        
        return True
    except Exception as e:
        print(f'   ❌ Errore: {e}')
        return False
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    # Analisi database
    root_exists, backend_exists = analyze_databases()
    
    # Test applicazione
    app_works = test_app_database()
    backend_works = test_backend_database()
    
    print(f'\n📊 RIASSUNTO:')
    print(f'   Database ROOT esiste: {root_exists}')
    print(f'   Database BACKEND esiste: {backend_exists}')
    print(f'   App da ROOT funziona: {app_works}')
    print(f'   App da BACKEND funziona: {backend_works}')
    
    # Raccomandazioni
    print(f'\n💡 RACCOMANDAZIONI:')
    if backend_works and not app_works:
        print(f'   ✅ Il sistema usa il database in ./backend/carbonpilot.db')
        if root_exists:
            print(f'   🗑️ Puoi eliminare ./carbonpilot.db (non utilizzato)')
    elif app_works and not backend_works:
        print(f'   ✅ Il sistema usa il database in ./carbonpilot.db')
        if backend_exists:
            print(f'   🗑️ Puoi eliminare ./backend/carbonpilot.db (non utilizzato)')
    else:
        print(f'   ⚠️ Configurazione ambigua - verifica manualmente') 