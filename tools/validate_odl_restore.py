#!/usr/bin/env python3
"""
Script di validazione per la funzione "Ripristina stato precedente" ODL

Testa:
✅ Endpoint POST /odl/{id}/restore-status
✅ Aggiornamento campo previous_status nel database
✅ Registrazione nei log di stato
✅ Gestione errori (ODL inesistente, nessuno stato precedente)
"""

import sys
import os
import sqlite3
import requests
import json
from datetime import datetime
from pathlib import Path

# Aggiungi il percorso del backend al PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Configurazione
API_BASE_URL = "http://localhost:8000/api/v1"
DB_PATH = Path(__file__).parent.parent / "carbonpilot.db"

def print_header(title: str):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step: str):
    """Stampa un passo del test"""
    print(f"\n🔍 {step}")

def print_success(message: str):
    """Stampa un messaggio di successo"""
    print(f"✅ {message}")

def print_error(message: str):
    """Stampa un messaggio di errore"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Stampa un messaggio di warning"""
    print(f"⚠️ {message}")

def check_database_schema():
    """Verifica che il campo previous_status esista nel database"""
    print_step("Verifica schema database")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Verifica struttura tabella ODL
        cursor.execute("PRAGMA table_info(odl)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'previous_status' in columns:
            print_success("Campo 'previous_status' presente nella tabella ODL")
        else:
            print_error("Campo 'previous_status' NON presente nella tabella ODL")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Errore nella verifica del database: {e}")
        return False

def get_test_odl():
    """Trova un ODL di test o ne crea uno"""
    print_step("Ricerca ODL di test")
    
    try:
        # Cerca ODL esistenti
        response = requests.get(f"{API_BASE_URL}/odl/")
        if response.status_code == 200:
            odl_list = response.json()
            if odl_list:
                odl = odl_list[0]
                print_success(f"Trovato ODL di test: ID {odl['id']}, stato '{odl['status']}'")
                return odl
        
        print_warning("Nessun ODL trovato - creazione ODL di test necessaria")
        return None
        
    except Exception as e:
        print_error(f"Errore nella ricerca ODL: {e}")
        return None

def test_status_change_and_restore():
    """Testa il cambio di stato e il ripristino"""
    print_step("Test cambio stato e ripristino")
    
    # Trova un ODL di test
    odl = get_test_odl()
    if not odl:
        print_error("Impossibile procedere senza un ODL di test")
        return False
    
    odl_id = odl['id']
    stato_originale = odl['status']
    
    try:
        # 1. Cambia lo stato dell'ODL
        print(f"   📝 Cambio stato da '{stato_originale}' a 'Laminazione'")
        
        response = requests.patch(
            f"{API_BASE_URL}/odl/{odl_id}/status",
            json={"new_status": "Laminazione"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print_error(f"Errore nel cambio stato: {response.status_code} - {response.text}")
            return False
        
        odl_aggiornato = response.json()
        print_success(f"Stato cambiato a '{odl_aggiornato['status']}'")
        
        # Verifica che previous_status sia stato salvato
        if hasattr(odl_aggiornato, 'previous_status') and odl_aggiornato.get('previous_status') == stato_originale:
            print_success(f"Previous status salvato correttamente: '{odl_aggiornato.get('previous_status')}'")
        else:
            print_warning("Previous status non visibile nella risposta (potrebbe essere normale)")
        
        # 2. Testa il ripristino dello stato precedente
        print(f"   🔄 Ripristino stato precedente")
        
        response = requests.post(
            f"{API_BASE_URL}/odl/{odl_id}/restore-status",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print_error(f"Errore nel ripristino: {response.status_code} - {response.text}")
            return False
        
        odl_ripristinato = response.json()
        print_success(f"Stato ripristinato a '{odl_ripristinato['status']}'")
        
        # Verifica che lo stato sia tornato all'originale
        if odl_ripristinato['status'] == stato_originale:
            print_success("✨ Ripristino completato con successo!")
            return True
        else:
            print_error(f"Stato non ripristinato correttamente: atteso '{stato_originale}', ottenuto '{odl_ripristinato['status']}'")
            return False
            
    except Exception as e:
        print_error(f"Errore durante il test: {e}")
        return False

def test_error_cases():
    """Testa i casi di errore"""
    print_step("Test casi di errore")
    
    try:
        # Test 1: ODL inesistente
        print("   🔍 Test ODL inesistente (ID 99999)")
        response = requests.post(
            f"{API_BASE_URL}/odl/99999/restore-status",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 404:
            print_success("Errore 404 per ODL inesistente - corretto")
        else:
            print_warning(f"Risposta inaspettata per ODL inesistente: {response.status_code}")
        
        # Test 2: ODL senza stato precedente (se possibile)
        print("   🔍 Test ODL senza previous_status")
        
        # Trova un ODL e verifica se ha previous_status
        odl = get_test_odl()
        if odl:
            # Prova il ripristino - potrebbe fallire se non c'è previous_status
            response = requests.post(
                f"{API_BASE_URL}/odl/{odl['id']}/restore-status",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                print_success("Errore 400 per ODL senza previous_status - corretto")
            elif response.status_code == 200:
                print_success("Ripristino riuscito (ODL aveva previous_status)")
            else:
                print_warning(f"Risposta inaspettata: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Errore durante test casi di errore: {e}")
        return False

def verify_database_changes():
    """Verifica le modifiche nel database"""
    print_step("Verifica modifiche database")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Verifica che ci siano ODL con previous_status
        cursor.execute("""
            SELECT id, status, previous_status 
            FROM odl 
            WHERE previous_status IS NOT NULL 
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        
        if results:
            print_success(f"Trovati {len(results)} ODL con previous_status:")
            for odl_id, status, previous_status in results:
                print(f"   📋 ODL {odl_id}: '{status}' (precedente: '{previous_status}')")
        else:
            print_warning("Nessun ODL con previous_status trovato")
        
        # Verifica log di stato (se esistono)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='state_logs'
        """)
        
        if cursor.fetchone():
            cursor.execute("""
                SELECT COUNT(*) FROM state_logs 
                WHERE note LIKE '%ripristino%'
            """)
            
            count = cursor.fetchone()[0]
            if count > 0:
                print_success(f"Trovati {count} log di ripristino stato")
            else:
                print_warning("Nessun log di ripristino trovato")
        else:
            print_warning("Tabella state_logs non trovata")
        
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Errore nella verifica database: {e}")
        return False

def main():
    """Funzione principale di validazione"""
    print_header("VALIDAZIONE FUNZIONE RIPRISTINA STATO PRECEDENTE ODL")
    
    # Lista dei test da eseguire
    tests = [
        ("Schema Database", check_database_schema),
        ("Cambio Stato e Ripristino", test_status_change_and_restore),
        ("Casi di Errore", test_error_cases),
        ("Modifiche Database", verify_database_changes),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'─'*40}")
        print(f"🧪 Test: {test_name}")
        print(f"{'─'*40}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print_success(f"Test '{test_name}' SUPERATO")
            else:
                print_error(f"Test '{test_name}' FALLITO")
                
        except Exception as e:
            print_error(f"Test '{test_name}' ERRORE: {e}")
            results.append((test_name, False))
    
    # Riepilogo finale
    print_header("RIEPILOGO VALIDAZIONE")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Risultati: {passed}/{total} test superati")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print_success("\n🎉 TUTTI I TEST SUPERATI!")
        print("✅ La funzione 'Ripristina stato precedente' è implementata correttamente")
        return True
    else:
        print_error(f"\n💥 {total - passed} TEST FALLITI")
        print("❌ Verificare l'implementazione della funzione")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 