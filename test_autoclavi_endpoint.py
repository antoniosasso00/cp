#!/usr/bin/env python3
"""
🧪 Test dell'endpoint autoclavi per diagnosticare il problema
"""

import requests
import json
import sys
import os

# Cambia directory al backend per usare il database corretto
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append('.')

from models.db import SessionLocal
from models.autoclave import Autoclave
from sqlalchemy import text

def test_database_autoclavi():
    """Test diretto del database autoclavi"""
    
    print("🔍 TEST DATABASE AUTOCLAVI")
    print("="*50)
    
    db = SessionLocal()
    try:
        # Test conteggio totale
        total_autoclavi = db.query(Autoclave).count()
        print(f"📊 Totale autoclavi nel database: {total_autoclavi}")
        
        # Test stati diversi
        result = db.execute(text("SELECT stato, COUNT(*) FROM autoclavi GROUP BY stato"))
        stati_count = result.fetchall()
        
        print(f"\n📋 AUTOCLAVI PER STATO:")
        for stato, count in stati_count:
            print(f"   - '{stato}': {count} autoclavi")
        
        # Mostra alcune autoclavi
        result = db.execute(text("SELECT id, nome, codice, stato, lunghezza, larghezza_piano FROM autoclavi LIMIT 5"))
        autoclavi_sample = result.fetchall()
        
        print(f"\n🔍 PRIME 5 AUTOCLAVI:")
        for autoclave in autoclavi_sample:
            print(f"   - ID: {autoclave[0]} | Nome: '{autoclave[1]}' | Codice: '{autoclave[2]}' | Stato: '{autoclave[3]}'")
            print(f"     Dimensioni: {autoclave[4]}x{autoclave[5]}mm")
        
        return total_autoclavi > 0
        
    except Exception as e:
        print(f"❌ Errore database: {str(e)}")
        return False
    finally:
        db.close()

def test_autoclavi_api():
    """Test dell'endpoint API autoclavi"""
    
    print(f"\n🧪 TEST ENDPOINT API AUTOCLAVI")
    print("="*50)
    
    try:
        # URL dell'endpoint
        url = "http://localhost:8000/api/v1/autoclavi/"
        
        print(f"📡 Richiesta GET a: {url}")
        
        # Richiesta GET
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            autoclavi_count = len(data)
            
            print(f"✅ SUCCESSO!")
            print(f"   🏭 Autoclavi trovate dall'API: {autoclavi_count}")
            
            # Mostra alcune autoclavi
            if autoclavi_count > 0:
                print(f"\n🔍 PRIME 3 AUTOCLAVI DALL'API:")
                for i, autoclave in enumerate(data[:3]):
                    print(f"   {i+1}. ID: {autoclave.get('id')} | Nome: '{autoclave.get('nome')}' | Stato: '{autoclave.get('stato')}'")
                    print(f"      Dimensioni: {autoclave.get('lunghezza')}x{autoclave.get('larghezza_piano')}mm")
            else:
                print(f"⚠️ API restituisce lista vuota ma database ha dati")
            
            return True
            
        else:
            print(f"❌ ERRORE HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Dettagli: {error_data.get('detail', 'N/A')}")
            except:
                print(f"   Testo errore: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERRORE: Server non raggiungibile su localhost:8000")
        print(f"   💡 Il server FastAPI non è avviato")
        return False
        
    except Exception as e:
        print(f"❌ ERRORE API: {str(e)}")
        return False

def main():
    """Funzione principale"""
    
    print("🏭 DIAGNOSI PROBLEMI ENDPOINT AUTOCLAVI")
    print("="*60)
    
    # Test 1: Database
    db_ok = test_database_autoclavi()
    
    # Test 2: API (se server è disponibile)
    api_ok = test_autoclavi_api()
    
    print(f"\n" + "="*60)
    print(f"📊 RIASSUNTO DIAGNOSTICA:")
    print(f"   Database autoclavi: {'✅ OK' if db_ok else '❌ PROBLEMA'}")
    print(f"   API autoclavi: {'✅ OK' if api_ok else '❌ PROBLEMA'}")
    
    if db_ok and not api_ok:
        print(f"\n💡 DIAGNOSI:")
        print(f"   - Database contiene autoclavi")
        print(f"   - API non funziona correttamente")
        print(f"   - Possibile problema con filtro enum stato")
        print(f"   - Controllare mapping enum StatoAutoclaveEnum")
    elif not db_ok:
        print(f"\n💡 DIAGNOSI:")
        print(f"   - Database non contiene autoclavi")
        print(f"   - Aggiungere autoclavi di test")
    
    return api_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 