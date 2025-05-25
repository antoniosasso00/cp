#!/usr/bin/env python3
"""Script per verificare lo stato del database ODL e log"""

import sys
sys.path.append('.')

from sqlalchemy.orm import sessionmaker
from models.db import engine
from models.odl import ODL
from models.odl_log import ODLLog
from models.nesting_result import NestingResult

def main():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Verifica ODL esistenti
        odl_count = db.query(ODL).count()
        print(f'📊 ODL totali nel database: {odl_count}')
        
        # Verifica log esistenti
        log_count = db.query(ODLLog).count()
        print(f'📝 Log ODL totali nel database: {log_count}')
        
        # Verifica nesting esistenti
        nesting_count = db.query(NestingResult).count()
        print(f'🔧 Nesting totali nel database: {nesting_count}')
        
        # Mostra alcuni ODL di esempio con i loro stati
        print(f'\n📋 Esempi di ODL:')
        odl_examples = db.query(ODL).limit(5).all()
        for odl in odl_examples:
            print(f'  ODL {odl.id}: {odl.status} - Priorità: {odl.priorita}')
        
        # Mostra distribuzione per stato
        print(f'\n📈 Distribuzione ODL per stato:')
        from sqlalchemy import func
        stati = db.query(ODL.status, func.count(ODL.id)).group_by(ODL.status).all()
        for stato, count in stati:
            print(f'  {stato}: {count}')
            
    except Exception as e:
        print(f'❌ Errore: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    main() 