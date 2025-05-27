#!/usr/bin/env python3
"""
Script semplice per controllare la struttura del database
"""

import os
import sys

# Aggiungi il path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import SessionLocal
from sqlalchemy import text

def check_table_structure():
    """Controlla la struttura delle tabelle principali"""
    db = SessionLocal()
    
    try:
        tabelle = ['tools', 'cataloghi', 'parti', 'odl', 'autoclavi', 'cicli_cura']
        
        for tabella in tabelle:
            print(f"\n📋 Struttura tabella '{tabella}':")
            try:
                result = db.execute(text(f"PRAGMA table_info({tabella})"))
                colonne = result.fetchall()
                
                if colonne:
                    for colonna in colonne:
                        nome = colonna[1]
                        tipo = colonna[2]
                        nullable = "NULL" if colonna[3] == 0 else "NOT NULL"
                        print(f"   • {nome}: {tipo} ({nullable})")
                else:
                    print(f"   ⚠️ Tabella {tabella} non trovata o vuota")
                    
            except Exception as e:
                print(f"   ❌ Errore leggendo {tabella}: {str(e)}")
        
        # Controlla anche se ci sono dati
        print(f"\n📊 Conteggio record:")
        for tabella in tabelle:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {tabella}"))
                count = result.fetchone()[0]
                print(f"   • {tabella}: {count} record")
            except Exception as e:
                print(f"   • {tabella}: Errore - {str(e)}")
                
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 CONTROLLO STRUTTURA DATABASE")
    print("=" * 40)
    check_table_structure() 